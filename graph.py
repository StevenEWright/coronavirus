import sqlite3
import os
import csv
import datetime
import plotly.express as px

sqlite_file = ':memory:' # 'coronavirus.sqlite'
csv_directory = 'COVID-19/csse_covid_19_data/csse_covid_19_daily_reports'
csv_columns = ['Province/State','Country/Region','Last Update','Confirmed','Deaths','Recovered']

connection = sqlite3.connect(sqlite_file)
cursor = connection.cursor()

cursor.execute("CREATE TABLE population (country, population INTEGER);")
with open('population.csv', 'r') as fin:
  dr = csv.DictReader(fin)
  cursor.executemany("INSERT INTO population (country,population) VALUES (?, ?);", ([r['Country'], r['Population']] for r in dr))

cursor.execute("CREATE TABLE daily_reports (country, state, update_date, confirmed INTEGER, dead INTEGER, recovered INTEGER);")
directory = os.fsencode(csv_directory)
for file in os.listdir(directory):
  filename = os.fsdecode(file)
  if filename.endswith(".csv"):
    path = os.path.join(csv_directory, filename)
    with open(path,'r') as fin:
      dr = csv.DictReader(fin)
      for row in dr:
        has_columns = True
        for col in csv_columns:
          if col not in row.keys():
            print(f'Missing column: {col} in {file}')
            has_columns = False
            break
        if not has_columns:
            print(f'Found: {", ".join(row)}')
            break
        update_date_csv_value = row[csv_columns[2]].split(' ')[0].split('T')[0]
        update_date = ""
        if '/' in update_date_csv_value:
          update_date = datetime.datetime.strptime(update_date_csv_value, '%m/%d/%Y').strftime('%Y-%m-%d')
        else:
          update_date = datetime.datetime.strptime(update_date_csv_value, '%Y-%m-%d').strftime('%Y-%m-%d')
        cursor.execute("INSERT INTO daily_reports (country,state,update_date,confirmed,dead,recovered) VALUES (?, ?, ?, ?, ?, ?);", [row[csv_columns[1]], row[csv_columns[0]], update_date, row[csv_columns[3]], row[csv_columns[4]], row[csv_columns[5]]])
cursor.execute("UPDATE daily_reports SET country = 'Bahamas, The' WHERE country = 'The Bahamas';");
cursor.execute("UPDATE daily_reports SET country = 'Cabo Verde' WHERE country = 'Cape Verde';");
cursor.execute("UPDATE daily_reports SET country = 'China' WHERE country = 'Mainland China';");
cursor.execute("UPDATE daily_reports SET country = 'Czech Republic' WHERE country = 'Czechia';");
cursor.execute("UPDATE daily_reports SET country = 'Iran' WHERE country = 'Iran (Islamic Republic of)';");
cursor.execute("UPDATE daily_reports SET country = 'Republic of Korea' WHERE country = 'South Korea';");
cursor.execute("UPDATE daily_reports SET country = 'Republic of Korea' WHERE country = 'Korea, South';");
cursor.execute("UPDATE daily_reports SET country = 'Moldova' WHERE country = 'Republic of Moldova';");
cursor.execute("UPDATE daily_reports SET country = 'Russia' WHERE country = 'Russian Federation';");
cursor.execute("UPDATE daily_reports SET country = 'Saint Martin' WHERE country = 'St. Martin';");
cursor.execute("UPDATE daily_reports SET country = 'UK' WHERE country = 'United Kingdom';");
cursor.execute("UPDATE daily_reports SET country = 'Vietnam' WHERE country = 'Viet Nam';");
cursor.execute("UPDATE daily_reports SET country = 'Congo, Dem. Rep.' WHERE country = 'Congo (Kinshasa)';");
cursor.execute("UPDATE daily_reports SET country = 'Republic of the Congo' WHERE country = 'Congo (Brazzaville)';");

regular_data = []
normalized_data = []
records = []
daily_rows_cursor = connection.cursor()
country_rows = cursor.execute("SELECT population.country FROM population INNER JOIN daily_reports ON population.country = daily_reports.country WHERE population.population >= 10000000 and daily_reports.confirmed >= 100 GROUP BY population.country ORDER BY population.population DESC;")
for country_row in country_rows:
  country = country_row[0]
  daily_rows = daily_rows_cursor.execute("SELECT daily_reports.country as country, population.population as population, update_date, SUM(confirmed) as confirmed, SUM(dead) as dead, SUM(recovered) as recovered FROM daily_reports INNER JOIN population ON daily_reports.country = population.country WHERE daily_reports.country = ? GROUP BY daily_reports.country, update_date;", [ country ])
  cumulatives = []
  cumulative = 0
  last = 0
  cumulative_day = 0
  day = 0
  for daily_row in daily_rows:
    day = day + 1
    last = cumulative - int(daily_row[4]) - int(daily_row[5])
    cumulative = cumulative + (int(daily_row[3]) - last)
    regular_data.append({ 'Country': country, 'Day': daily_row[2], 'Confirmed Cases': cumulative })
    percent_of_population = 100 * cumulative / int(daily_row[1])
    if percent_of_population >= 0.001:
      cumulative_day = cumulative_day + 1
      cumulatives.append(percent_of_population)
      normalized_data.append({ 'Country': country, 'Days Since 0.02 Percent of Population are Confirmed Cases': cumulative_day, 'Confirmed Cases as Percent of Population': percent_of_population })
  records.append({ 'country': country, 'values': cumulatives })

connection.commit()
connection.close()

fig = px.line(normalized_data, x="Days Since 0.02 Percent of Population are Confirmed Cases", y="Confirmed Cases as Percent of Population", color='Country', title='Country Comparison')
fig.show()

fig2 = px.line(regular_data, x="Day", y="Confirmed Cases", color='Country', title='Confirmed Cases By Country') # , log_y=True
fig2.show()

