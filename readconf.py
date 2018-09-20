


if __name__ == "__main__":
    c = readconfig()
    con = f"{c['db']['dbdialect']}://{c['db']['user']}:{c['db']['pass']}@{c['db']['host']}:{c['db']['port']}/{c['db']['database']}"

    print(con)

