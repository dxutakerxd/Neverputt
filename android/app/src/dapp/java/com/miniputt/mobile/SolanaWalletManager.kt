/*
 * Copyright (C) 2026 MiniPutt Mobile Contributors
 *
 * NEVERBALL is  free software; you can redistribute  it and/or modify
 * it under the  terms of the GNU General  Public License as published
 * by the Free  Software Foundation; either version 2  of the License,
 * or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but
 * WITHOUT  ANY  WARRANTY;  without   even  the  implied  warranty  of
 * MERCHANTABILITY or  FITNESS FOR A PARTICULAR PURPOSE.   See the GNU
 * General Public License for more details.
 */

package com.miniputt.mobile

import android.content.ActivityNotFoundException
import android.net.Uri
import android.util.Log
import com.solana.mobilewalletadapter.clientlib.scenario.LocalAssociationIntentCreator
import com.solana.mobilewalletadapter.clientlib.scenario.LocalAssociationScenario
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONArray
import org.json.JSONObject
import java.util.concurrent.TimeUnit

object SolanaWalletManager {

    private const val TAG = "SolanaWalletManager"

    /* RPC endpoint — Solana public mainnet (replace with Helius key for production) */
    private const val RPC_URL = "https://api.mainnet-beta.solana.com"

    /* Token-2022 program ID */
    private const val TOKEN_2022_PROGRAM = "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"

    /* Seeker Genesis Token identifiers */
    private const val SGT_MINT_AUTHORITY = "GT2zuHVaZQYZSyQMgJPLzvkmyztfyXg2NJunqFp4p3A4"
    private const val SGT_METADATA_POINTER = "GT22s89nU4iWFkNXj1Bw6uYhJJWDRPpShHt4Bk8f99Te"

    private const val ASSOCIATION_TIMEOUT_MS = 60000
    private const val SCENARIO_TIMEOUT_S = 60L
    private const val CLOSE_TIMEOUT_S = 10L

    /*
     * State machine (matches ad_rewarded_state pattern):
     *   0 = disconnected
     *   1 = connecting (MWA intent fired, waiting)
     *   2 = connected, verifying SGT
     *   3 = connected, SGT verified (Seeker owner)
     *   4 = connected, no SGT (regular wallet)
     *   5 = error/failed
     */
    @Volatile
    private var state: Int = 0

    @Volatile
    private var pubkey: String = ""

    private val httpClient = OkHttpClient.Builder()
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(15, TimeUnit.SECONDS)
        .build()

    private val scope = CoroutineScope(Dispatchers.Main)

    @JvmStatic
    fun init() {
        Log.i(TAG, "SolanaWalletManager initialized")
    }

    @JvmStatic
    fun connect() {
        val activity = MySDLActivity.getActivity() ?: run {
            Log.e(TAG, "No activity available")
            state = 5
            return
        }

        state = 1

        scope.launch {
            var scenario: LocalAssociationScenario? = null

            try {
                val publicKeyBytes = withContext(Dispatchers.IO) {
                    val sc = LocalAssociationScenario(ASSOCIATION_TIMEOUT_MS)
                    scenario = sc

                    val associationIntent =
                        LocalAssociationIntentCreator.createAssociationIntent(
                            null,
                            sc.port,
                            sc.session
                        )

                    /* Launch wallet app on UI thread */
                    withContext(Dispatchers.Main) {
                        activity.startActivity(associationIntent)
                    }

                    /* Wait for wallet to connect back via local WebSocket */
                    Log.d(TAG, "Waiting for wallet app to connect...")
                    val client = sc.start()
                        .get(SCENARIO_TIMEOUT_S, TimeUnit.SECONDS)

                    Log.d(TAG, "Wallet connected, sending authorize...")
                    val authResult = client.authorize(
                        Uri.parse("https://miniputt.com"),
                        Uri.parse("favicon.ico"),
                        "MiniPutt Mobile",
                        "mainnet-beta"
                    ).get(SCENARIO_TIMEOUT_S, TimeUnit.SECONDS)

                    val pk = authResult.accounts.first().publicKey

                    Log.d(TAG, "Raw publicKey bytes (${pk.size}): ${pk.joinToString(",") {
                        String.format("%02x", it)
                    }}")

                    sc.close().get(CLOSE_TIMEOUT_S, TimeUnit.SECONDS)
                    scenario = null

                    pk
                }

                pubkey = base58Encode(publicKeyBytes)
                Log.i(TAG, "Base58 pubkey: $pubkey")
                Log.i(TAG, "Pubkey length: ${pubkey.length} chars, " +
                           "raw bytes: ${publicKeyBytes.size}")
                state = 2

                /* Verify SGT ownership on IO thread */
                Log.d(TAG, "Verifying SGT for $pubkey ...")
                val hasToken = withContext(Dispatchers.IO) {
                    verifySeekerToken(pubkey)
                }

                state = if (hasToken) 3 else 4
                Log.i(TAG, "Verification complete: state=$state, " +
                           "isSeeker=${hasToken}")

            } catch (e: ActivityNotFoundException) {
                Log.e(TAG, "No wallet app installed", e)
                state = 5
            } catch (e: java.util.concurrent.TimeoutException) {
                Log.e(TAG, "Wallet connection timed out", e)
                state = 5
            } catch (e: java.util.concurrent.ExecutionException) {
                /* User cancelled or wallet rejected */
                Log.w(TAG, "Wallet authorization cancelled/rejected: ${e.cause?.message}")
                state = 5
            } catch (e: java.util.concurrent.CancellationException) {
                Log.w(TAG, "Wallet connection cancelled", e)
                state = 5
            } catch (e: Exception) {
                Log.e(TAG, "Wallet connection failed: ${e.javaClass.simpleName}", e)
                state = 5
            } finally {
                /* Always close the scenario to avoid hanging */
                try {
                    scenario?.close()
                } catch (_: Exception) { }
            }
        }
    }

    @JvmStatic
    fun getState(): Int = state

    @JvmStatic
    fun isSeeker(): Boolean = state == 3

    @JvmStatic
    fun getPubkey(): String = pubkey

    @JvmStatic
    fun disconnect() {
        state = 0
        pubkey = ""
    }

    /* ------------------------------------------------------------------ */
    /* RPC helpers                                                         */
    /* ------------------------------------------------------------------ */

    private fun verifySeekerToken(owner: String): Boolean {
        try {
            val mints = getTokenMints(owner)
            Log.d(TAG, "Found ${mints.size} Token-2022 mints for $owner")

            for (mint in mints) {
                Log.d(TAG, "Checking mint: $mint")
                if (checkMintIsSGT(mint)) {
                    Log.i(TAG, "SGT MATCH: $mint")
                    return true
                }
            }
            Log.d(TAG, "No SGT found among ${mints.size} mints")
        } catch (e: Exception) {
            Log.e(TAG, "SGT verification RPC error", e)
        }
        return false
    }

    /**
     * Get all Token-2022 token mints owned by the given pubkey.
     */
    private fun getTokenMints(owner: String): List<String> {
        val body = JSONObject().apply {
            put("jsonrpc", "2.0")
            put("id", 1)
            put("method", "getTokenAccountsByOwner")
            put("params", JSONArray().apply {
                put(owner)
                put(JSONObject().put("programId", TOKEN_2022_PROGRAM))
                put(JSONObject().put("encoding", "jsonParsed"))
            })
        }

        Log.d(TAG, "RPC getTokenAccountsByOwner request for $owner")
        val response = rpcCall(body)

        /* Check for RPC-level error */
        val rpcError = response.optJSONObject("error")
        if (rpcError != null) {
            Log.e(TAG, "RPC error: ${rpcError.toString()}")
            return emptyList()
        }

        val result = response.optJSONObject("result")
        if (result == null) {
            Log.w(TAG, "RPC response missing 'result': ${response.toString().take(500)}")
            return emptyList()
        }

        val value = result.optJSONArray("value")
        if (value == null) {
            Log.w(TAG, "RPC result missing 'value': ${result.toString().take(500)}")
            return emptyList()
        }

        Log.d(TAG, "getTokenAccountsByOwner returned ${value.length()} accounts")

        val mints = mutableListOf<String>()
        for (i in 0 until value.length()) {
            try {
                val account = value.getJSONObject(i)
                val parsed = account
                    .getJSONObject("account")
                    .getJSONObject("data")
                    .getJSONObject("parsed")
                    .getJSONObject("info")
                val mint = parsed.getString("mint")
                val amount = parsed.optString("tokenAmount", "")
                Log.d(TAG, "  token[$i]: mint=$mint amount=$amount")
                mints.add(mint)
            } catch (e: Exception) {
                Log.w(TAG, "  token[$i]: parse error: ${e.message}")
            }
        }
        return mints
    }

    /**
     * Check if a mint matches SGT criteria:
     *   - mintAuthority == SGT_MINT_AUTHORITY
     *   - Has metadata pointer extension matching SGT_METADATA_POINTER
     */
    private fun checkMintIsSGT(mint: String): Boolean {
        val body = JSONObject().apply {
            put("jsonrpc", "2.0")
            put("id", 1)
            put("method", "getAccountInfo")
            put("params", JSONArray().apply {
                put(mint)
                put(JSONObject().apply {
                    put("encoding", "jsonParsed")
                })
            })
        }

        Log.d(TAG, "RPC getAccountInfo for mint $mint")
        val response = rpcCall(body)

        val rpcError = response.optJSONObject("error")
        if (rpcError != null) {
            Log.e(TAG, "RPC error for mint $mint: ${rpcError.toString()}")
            return false
        }

        val result = response.optJSONObject("result") ?: return false
        val value = result.optJSONObject("value") ?: return false
        val data = value.optJSONObject("data") ?: return false
        val parsed = data.optJSONObject("parsed") ?: return false
        val info = parsed.optJSONObject("info") ?: return false

        /* Check mint authority */
        val mintAuth = info.optString("mintAuthority", "")
        Log.d(TAG, "  mintAuthority: $mintAuth")
        Log.d(TAG, "  expected:      $SGT_MINT_AUTHORITY")
        Log.d(TAG, "  match: ${mintAuth == SGT_MINT_AUTHORITY}")

        if (mintAuth != SGT_MINT_AUTHORITY)
            return false

        /* Check extensions for metadata pointer or group membership */
        val extensions = info.optJSONArray("extensions")
        Log.d(TAG, "  extensions: ${extensions?.length() ?: 0}")

        if (extensions != null) {
            for (i in 0 until extensions.length()) {
                val ext = extensions.getJSONObject(i)
                val extType = ext.optString("extension", "")
                Log.d(TAG, "  ext[$i]: type=$extType")

                if (extType == "metadataPointer") {
                    val extState = ext.optJSONObject("state")
                    val authority = extState?.optString("authority", "") ?: ""
                    val metadataAddress = extState?.optString("metadataAddress", "") ?: ""
                    Log.d(TAG, "    metadataPointer authority=$authority")
                    Log.d(TAG, "    metadataPointer metadataAddress=$metadataAddress")
                    if (authority == SGT_METADATA_POINTER ||
                        metadataAddress == SGT_METADATA_POINTER) {
                        return true
                    }
                }
                if (extType == "tokenGroupMember") {
                    val extState = ext.optJSONObject("state")
                    val group = extState?.optString("group", "") ?: ""
                    Log.d(TAG, "    tokenGroupMember group=$group")
                    if (group == SGT_METADATA_POINTER) {
                        return true
                    }
                }
            }
        }

        return false
    }

    private fun rpcCall(body: JSONObject): JSONObject {
        val mediaType = "application/json".toMediaType()
        val request = Request.Builder()
            .url(RPC_URL)
            .post(body.toString().toRequestBody(mediaType))
            .build()

        val response = httpClient.newCall(request).execute()
        val responseBody = response.body?.string() ?: "{}"
        Log.d(TAG, "RPC response (${response.code}): ${responseBody.take(1000)}")
        return JSONObject(responseBody)
    }

    /* ------------------------------------------------------------------ */
    /* Base58 encoding (Bitcoin alphabet)                                   */
    /* ------------------------------------------------------------------ */

    private const val ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

    private fun base58Encode(input: ByteArray): String {
        if (input.isEmpty()) return ""

        val data = input.copyOf()

        /* Count leading zero bytes */
        var zeros = 0
        for (b in data) {
            if (b.toInt() == 0) zeros++ else break
        }

        val encoded = CharArray(data.size * 2)
        var outputStart = encoded.size

        var start = zeros
        while (start < data.size) {
            /* Use Int division — process one byte at a time so carry
             * never exceeds 255*256+255 = 65535+255 = 65790, well
             * within Int range. Each iteration: carry = carry*256 + byte
             * where carry is the remainder from the previous byte (0..57),
             * so max is 57*256+255 = 14847. */
            var remainder = 0
            var i = start
            while (i < data.size) {
                val digit = data[i].toInt() and 0xFF
                val temp = remainder * 256 + digit
                data[i] = (temp / 58).toByte()
                remainder = temp % 58
                i++
            }
            outputStart--
            encoded[outputStart] = ALPHABET[remainder]

            /* Skip leading zeros in the working buffer */
            while (start < data.size && data[start].toInt() == 0) {
                start++
            }
        }

        /* Prepend '1' for each leading zero byte in input */
        for (i in 0 until zeros) {
            outputStart--
            encoded[outputStart] = '1'
        }

        return String(encoded, outputStart, encoded.size - outputStart)
    }
}
