import psycopg2
import csv
import os
import pandas as pd
from os import listdir
from psycopg2.extensions import AsIs


#Put your postgres password here if different
password = 'PASSWORD'
outputDir = './data/processed/'


def setup_database():
    filenames = find_csv_filenames(f'{outputDir}')
    for fileName in filenames:
        print(fileName)
        tableName  = os.path.basename(fileName).split(".")[0]
        print(tableName)

        with open(f'{outputDir}{fileName}', 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            columns = next(reader)
        columnString = ", ".join(columns)
        print(columnString)
        
        conn = psycopg2.connect(f"host=localhost dbname=postgres user=postgres password={password}")
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE %s(
        %s)
        """,
        [AsIs(tableName), AsIs(columnString),])
        conn.commit()

        with open(f'{outputDir}{fileName}', 'r', encoding='utf-8-sig') as f:
            next(f) # Skip the header row.
            cur.copy_from(f, f'{tableName}', sep=',')
        conn.commit()

        cur.close()
        conn.close()


def find_csv_filenames(path_to_dir, suffix=".csv"):
    filenames = listdir(path_to_dir)
    return [ filename for filename in filenames if filename.endswith( suffix ) ]


def drop_table(tableName):
    conn = psycopg2.connect(f"host=localhost dbname=postgres user=postgres password={password}")
    cur = conn.cursor()
    cur.execute("""
    DROP TABLE %s;
    """,
    [AsIs(tableName),])
    conn.commit()
    cur.close()
    conn.close()
    

def drop_all_tables():
    filenames = find_csv_filenames(f'{outputDir}')
    tableNames = []
    for fileName in filenames:
        tableNames.append(os.path.basename(fileName).split(".")[0])

    tableString = ", ".join(tableNames)
    print("Dropping tables: " + tableString)

    conn = psycopg2.connect(f"host=localhost dbname=postgres user=postgres password={password}")
    cur = conn.cursor()
    cur.execute("""
    DROP TABLE %s;
    """,
    [AsIs(tableString),])
    conn.commit()
    cur.close()
    conn.close()


def get_id(county, state, country):
    conn = psycopg2.connect(f"host=localhost dbname=postgres user=postgres password={password}")
    cur = conn.cursor()
    cur.execute("""
    SELECT county_code FROM county_codes WHERE county_name = '%s' AND state = '%s' AND country = '%s';
    """,
    [AsIs(county), AsIs(state), AsIs(country)])
    conn.commit()
    results = cur.fetchone()
    if results is not None:
        results = str(results[0])
        if len(results)< 7:
            results = f'0{results}'
        print(results)
    else:
        print("No id was found for given country, state and county") 
        results = ""

    cur.close()
    conn.close()
    return results

def get_ids_by_state(state, country):
    conn = psycopg2.connect(f"host=localhost dbname=postgres user=postgres password={password}")
    cur = conn.cursor()
    cur.execute("""
    SELECT county_code FROM county_codes WHERE state = '%s' AND country = '%s';
    """,
    [AsIs(state), AsIs(country)])
    conn.commit()
    results = cur.fetchall()
    formatted_results = []
    if cur.rowcount != 0:
        for row in results:
            if len(str(row[0]))< 7:
                formatted_results.append(f'0{row[0]}')
    else:
        print("No ids were found for given country and state")

    print(formatted_results)
    cur.close()
    conn.close()
    return formatted_results


def get_ids_by_country(country):
    conn = psycopg2.connect(f"host=localhost dbname=postgres user=postgres password={password}")
    cur = conn.cursor()
    cur.execute("""
    SELECT county_code FROM county_codes WHERE country = '%s';
    """,
    [AsIs(country)])
    conn.commit()
    results = cur.fetchall()
    formatted_results = []
    if cur.rowcount != 0:
        for row in results:
            if len(str(row[0]))< 7:
                formatted_results.append(f'0{row[0]}')
    else:
        print("No ids were found for given country")

    print(formatted_results)
    cur.close()
    conn.close()
    return formatted_results


#tableName, columnList and idList must be sent in as strings or lists of strings. Years are integers. 
def get_data(tableName, columnList, idList, startYear, endYear):
    columnString = ", ".join(columnList)
    idYearList = []
    
    for year in range(startYear, endYear+1):
        for dataId in idList:
            idYearList.append(dataId+str(year))
        
    idString = ", ".join(idYearList)

    print("Fetching ids: ")
    print(idYearList)

    conn = psycopg2.connect(f"host=localhost dbname=postgres user=postgres password={password}")
    cur = conn.cursor()
    cur.execute("""
    SELECT %s FROM %s WHERE id IN (%s);
    """,
    [AsIs(columnString), AsIs(tableName), AsIs(idString)])
    conn.commit()
    results = cur.fetchall()
    cur.close()
    conn.close()
    df = pd.DataFrame(data=results, columns=cols)
    print(df)

    return df


def get_data_for_single_county(columnList, county, state, country, startYear, endYear):
        tableName = "weather"
        county_id = get_id(county, state, country)
        idList = []
        idList.append(county_id)
        return get_data(tableName, columnList, idList, startYear, endYear)

def get_data_for_state(columnList, state, country, startYear, endYear):
        tableName = "weather"
        idList = get_ids_by_state(state, country)
        return get_data(tableName, columnList, idList, startYear, endYear)

def get_data_for_country(columnList, country, startYear, endYear):
        tableName = "weather"
        idList = get_ids_by_country(country)
        return get_data(tableName, columnList, idList, startYear, endYear)


#setup_database()

tableName = "weather"
columnList = ["id", "tmp_avg_jan"]
idList = ["0101001", "0101005"]
startYear = 1990
endYear = 1995
county = "Baldwin"
state = "AL"
country = "US"
#get_data_for_single_county(columnList, county, state, country, startYear, endYear)
#get_data_for_state(columnList, state, country, startYear, endYear)
get_data_for_country(columnList, country, startYear, endYear)




setup_database()

