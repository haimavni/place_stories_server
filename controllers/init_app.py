def init_database():
    password = request.vars.password
    email = request.vars.email
    #these values are passed from the hub application. if they exist, create the owner account with all privileges
    return "database initialized"