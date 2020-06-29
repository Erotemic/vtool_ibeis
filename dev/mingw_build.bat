SET ORIGINAL=%CD%
@echo off

:: TODO: Find out why openmp doesn't work

:: helper variables
call :build_sver
goto :exit

:build_sver
:: helper variables
set INSTALL32=C:\Program Files (x86)

mkdir build
cd build

@echo on
cmake ^
-G "MSYS Makefiles" ^
-DOpenCV_DIR="%INSTALL32%\OpenCV" ^
.. && make

copy /y libsver.dll.a ..\vtool

copy /y libsver.dll ..\vtool
@echo off

:: -DCMAKE_C_FLAGS="-march=i486" ^
:: -DCMAKE_CXX_FLAGS="-march=i486" ^
:: make command that doesn't freeze on mingw
:: mingw32-make -j7 "MAKE=mingw32-make -j3" -f CMakeFiles\Makefile2 all
exit /b

:exit
cd %ORIGINAL%
@echo on
exit /b
