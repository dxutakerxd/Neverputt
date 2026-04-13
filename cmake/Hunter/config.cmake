# Fix SDL2 compilation with modern NDK compilers
# SDL2 checks for -Werror=declaration-after-statement support and enables it,
# but its own source files violate this. Override the check result to prevent it.
if(ANDROID)
    hunter_config(
        SDL2
        VERSION 2.0.22-22d6e09
        CMAKE_ARGS
            HAVE_GCC_WERROR_DECLARATION_AFTER_STATEMENT=FALSE
            HAVE_GCC_WDECLARATION_AFTER_STATEMENT=FALSE
            SDL_HIDAPI=OFF
    )
elseif(IOS)
    hunter_config(
        SDL2
        VERSION 2.0.22-22d6e09
        CMAKE_ARGS
            SDL_HIDAPI=NO
    )
endif()
