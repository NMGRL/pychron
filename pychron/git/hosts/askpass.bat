
if "%1:~0,8%" == "username" (
    echo %GIT_ASKPASS_USERNAME%
)

if "%1:~0,8%" == "password" (
    echo %GIT_ASKPASS_PASSWORD%
)

