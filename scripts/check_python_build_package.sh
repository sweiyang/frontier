#!/bin/bash
echo "----"
python -m twine check dist/*
echo "----"
python -c "import zipfile, glob; 
p=glob.glob('dist/*.whl')[0]; 
z=zipfile.ZipFile(p); 
print('\n'.join(z.namelist()[:200]))"