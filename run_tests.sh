"""
Runs all tests

Bubble text from:
http://patorjk.com/software/taag/#p=display&f=Cybermedium&t=VTOOL%20TESTS
"""
# TODO: MAKE SURE IBS DATABASE CAN HANDLE WHEN IMAGE PATH IS NOT WHERE IT EXPECTED
# TODO: ADD CACHE / LOCALIZE IMAGES IN IBEIS CONTROL

# Win32 path hacks
export CWD=$(pwd)

# FIXME: Weird directory dependency
#export PATHSEP=$(python -c "import os; print(os.pathsep)")
export PY=python
#export PY=python2.7
export PYHESAFF_DIR=$($PY -c "import os, pyhesaff; print(os.path.dirname(pyhesaff.__file__))")
export VTOOL_DIR=$($PY -c "import os, vtool; print(os.path.dirname(vtool.__file__))")
echo $VTOOL_DIR
echo $PYTHONPATH

export ARGV="--quiet --noshow $@"


PRINT_DELIMETER(){
    printf "\n#\n#\n#>>>>>>>>>>> next_test\n\n"
}


BEGIN_TESTS()
{
    echo "BEGIN: ARGV=$ARGV"
    PRINT_DELIMETER

    num_passed=0
    num_ran=0

    export FAILED_TESTS=''
}

RUN_TEST()
{
    echo "RUN_TEST: $@"
    export TEST="$PY $@ $ARGV"
    $TEST
    export RETURN_CODE=$?
    PRINT_DELIMETER
    num_passed=$(($num_passed + (1 - $RETURN_CODE)))
    num_ran=$(($num_ran + 1))

    if [ "$RETURN_CODE" != "0" ] ; then
        export FAILED_TESTS="$FAILED_TESTS\n$TEST"
    fi

}

END_TESTS()
{
    echo "RUN_TESTS: DONE"

    if [ "$FAILED_TESTS" != "" ] ; then
        echo "-----"
        printf "Failed Tests:" 
        printf "$FAILED_TESTS\n"
        printf "$FAILED_TESTS\n" >> failed.txt
        echo "-----"
    fi
    echo "$num_passed / $num_ran tests passed"
}

#---------------------------------------------
# START TESTS
BEGIN_TESTS

#---------------------------------------------
# VTOOL TESTS
export VTOOL_TESTS="ON"
if [ "$VTOOL_TESTS" = "ON" ] ; then 
cat <<EOF
    _  _ ___ ____ ____ _       ___ ____ ____ ___ ____ 
    |  |  |  |  | |  | |        |  |___ [__   |  [__  
     \/   |  |__| |__| |___     |  |___ ___]  |  ___] 
EOF
    RUN_TEST $VTOOL_DIR/tests/test_draw_keypoint.py --noshow 
    RUN_TEST $VTOOL_DIR/tests/test_exhaustive_ori_extract.py --noshow 
    RUN_TEST $VTOOL_DIR/tests/test_vtool.py 
    RUN_TEST $VTOOL_DIR/tests/test_akmeans.py 
    RUN_TEST $VTOOL_DIR/tests/test_spatial_verification.py --noshow 
    RUN_TEST $VTOOL_DIR/tests/time_cythonized_funcs.py 
fi


python -c "import utool; print('\n'.join(utool.glob('~/code/vtool/', 'test_*.py', recursive=True, verbose=True)))"
python -c "import utool; print(      len(utool.glob('~/code/vtool/', 'test_*.py', recursive=True, verbose=True)))"

python -c "import utool; print('\n'.join(utool.glob('~/code/ibeis/', 'test_*.py', recursive=True, verbose=True)))"
#---------------------------------------------
# END TESTING
END_TESTS

