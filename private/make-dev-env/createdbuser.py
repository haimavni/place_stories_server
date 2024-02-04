import os
from dotenv import load_dotenv

def get_env_var(var_name):            
    load_dotenv('/home/haim/web2py/.env')
    return os.getenv(var_name)

db_user = get_env_var("DB_USER")
db_password = get_env_var("DB_PASSWORD")
cmd = f"sudo -i -u postgres psql -c \"create user {db_user} with encrypted password '{db_password}'\""
print("Execute the command below:")
print(f"{cmd}")