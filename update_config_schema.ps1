# generate pydantic model and save schema to:
# project\config_model\config_schema.json

# pushd
Set-Location project\config_model

python config_pydantic.py

# popd
Set-Location ..\..
