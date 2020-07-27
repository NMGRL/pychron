@set arg=%~1
@if (%arg:~0,8%)==(Username) echo %GIT_ASKPASS_USERNAME%
@if (%arg:~0,8%)==(Password) echo %GIT_ASKPASS_PASSWORD%

