import mysql.connector
import random
import time
import sys


def connect_met_database():
    """
    In deze functie meld je je aan aan de sql database, deze functie wordt vaker in het programma opgeroepen door andere
    functies.  Je returned de connectie in de cursor om opdrachten mee uit te voeren.

    :return connectie, cursor:
    """


    #Variabele om in te loggen
    host_naam = "localhost"
    gebruikersnaam = "root"
    ww = ""
    global database_naam
    database_naam = "test"

    #connectie met de database
    connectie = mysql.connector.connect(host=host_naam,
                                        user=gebruikersnaam,
                                        password=ww,
                                        database=database_naam)
    cursor = connectie.cursor()

    return connectie, cursor

def database_sluiten(connectie, cursor):
    """
    Hier sluit je de cursor, commit je data en sluit je daarna ook de database. Ook deze functie wordt alleen door
    andere functies opgeroepen.
    :param connectie:
    :param cursor:
    """

    cursor.close()
    connectie.commit()
    connectie.close()

def maak_tabellen_aan(cursor):
    """
    Deze functie is die die de tabellen in de database aanmaakt. Hij maakt plaats voor het ID van de 4 producten per
    recommendation die je later aan de tabellen gaat toevoegen.
    :param cursor:
    """
    cursor.execute("USE " + database_naam)
    cursor.execute("CREATE TABLE content (id VARCHAR(255) PRIMARY KEY UNIQUE, product1 VARCHAR(255) NULL, product2 VARCHAR(255) NULL, product3 VARCHAR(255) NULL, product4 VARCHAR(255) NULL)")
    cursor.execute("CREATE TABLE collaborative (id VARCHAR(255) PRIMARY KEY UNIQUE, product1 VARCHAR(255) NULL, product2 VARCHAR(255) NULL, product3 VARCHAR(255) NULL, product4 VARCHAR(255) NULL)")

def verwijder_tabellen(cursor):
    """
    Deze functie verwijderd de tabellen van de recommendations die zijn gemaakt.
    :param cursor
    """
    cursor.execute("USE " + database_naam)
    cursor.execute("DROP TABLE content")
    cursor.execute("DROP TABLE collaborative")

def data_ophalen_uit_database(cursor, profiel_id):
    """
    functie voor het krijgen en returnen van profiel_data
    :return profiel_data
    :param cursor, profiel_id
    """

    cursor.execute("SELECT products.id,products.price,products.stock,main_category.id,orders.aantal,brand.brand,gender.id,orders.sessions_id_key,doelgroep.id,sessions.profiles_id_key FROM `products`,`brand`,`gender`,`orders`,`main_category`,`sessions`,`doelgroep` WHERE products.gender_id_key = gender.id AND products.main_category_id_key = main_category.id AND products.brand_id_key = brand.id AND orders.products_id_key = products.id AND products.doelgroep_id_key = doelgroep.id AND orders.sessions_id_key = sessions.id AND profiles_id_key = '%s'" % profiel_id)
    profiel_data = cursor.fetchall()

    return profiel_data



def sorteer_data_collaborative(cursor, profiel_id):
    """
    functie voor het maken van collaborative recommendation gebasseerd op vergelijkbaren profielen
    :param cursor
    :param profiel_id
    :return profiel_id
    """
    #lege listst die gevuld zullen worden
    product_idx = []
    profiel_idx = []

    # Ophalen data uit database
    profiel_data = data_ophalen_uit_database(cursor, profiel_id)

    # Ophalen van de specifieke data die we nodig hebben voor deze recommendation, en toevoegen aan een list. In dit
    # geval van alle categorieen, gender = vrouwen, en als doelgroep specifiek weer vrouwen.
    for i in profiel_data:
        cursor.execute("SELECT products.id,products.gender_id_key,products.main_category_id_key,products.doelgroep_id_key,sessions.profiles_id_key FROM `products`,`orders`,`profiles`,`sessions` WHERE orders.products_id_key = products.id AND sessions.profiles_id_key = profiles.id AND orders.sessions_id_key = sessions.id AND main_category_id_key = '{0}' AND gender_id_key = '{12}' AND doelgroep_id_key = '{16}'".format(i[4], i[6], i[7]))
        manderijn = cursor.fetchall()

        for i in manderijn:
            profiel_idx.append(i[4])

    # alle data ophalen van een random profiel dat vergelijkbaar is met de profielen uit onze mandarijn list. (Ik ben een mandarijntje aan het eten vandaar de naam)
    cursor.execute("SELECT products.id, products.price, products.stock, orders.aantal, main_category.id, brand.brand, gender.id, doelgroep.id, orders.sessions_id_key, sessions.profiles_id_key FROM `products`, `gender`, `brand`, `main_category`, `orders`, `sessions`, `doelgroep` WHERE products.gender_id_key = gender.id AND products.brand_id_key = brand.id AND products.main_category_id_key = main_category.id AND orders.products_id_key = products.id AND orders.sessions_id_key = sessions.id AND products.doelgroep_id_key = doelgroep.id AND profiles_id_key = '%s'" % ''.join(random.sample(profiel_idx, 1)))
    profiel_data = cursor.fetchall()

    for i in profiel_data:
        product_idx.append(i[0])


    return profiel_id, random.sample(product_idx, 4)


def sorteer_data_content(cursor, profiel_id):
    """
    functie voor het maken van content recommendation gebasseerd op producten die lijken op wat er laats is gekocht
    :param cursor
    :param profielid
    :return profiel_id, random 4 recommendated products
    """

    product_idx = []

    # Ophalen data uit database
    profiel_data = data_ophalen_uit_database(cursor, profiel_id)

    # Ophalen van de specifieke data die we nodig hebben voor deze recommendation, en toevoegen aan een list. In dit
    # geval van alle categorieen, gender = vrouwen, en als doelgroep specifiek zwangere vrouwen.
    for i in profiel_data:
        cursor.execute("SELECT `id`, `main_category_id_key`, `gender_id_key`, `doelgroep_id_key` FROM `products` WHERE main_category_id_key = '{0}' AND gender_id_key = '{12}' AND doelgroep_id_key = '{4}'".format(i[4], i[6], i[7]))
        vrouwen_recommendation = cursor.fetchall()

    for i in vrouwen_recommendation:
        product_idx.append(i[0])

    #return profiel_id en 4 random producten ID's uit de lijst met vergelijkbare producten uit die categorie
    return profiel_id, random.sample(product_idx, 4)

def data_storten(profiel, waarde, connectie, cursor, tabel, *rij):
    """
    Connect aan de database en loop door de verschillende waardes in de list en voeg ze die dan toe aan de table collums.
    Execute deze command en commit het naar de sql database.
    :param direction:, :param profile, :param list_value:, :param db:, :param cursor:, :param table:, :param *column:, :return:,
    """
    tomaat = True

    while tomaat:
        nieuwe_tabel = "INSERT IGNORE INTO " + tabel + " ("+[0]+", "+rij[1]+","+rij[2]+","+rij[3]+", "+rij[4] +") VALUES (%, %, %, %, %)"
        sorteren = (str(profiel), str(waarde[0]), str(waarde[1]), str(waarde[2]), str(waarde[3]))
        cursor.execute(nieuwe_tabel, sorteren)
        connectie.commit()
        tomaat = False

def recommendation_engine():
    """
    Deze functie zet alles op gang & timed het process

    :return
    """
    start = time.time()
    #connect aan de database, verwijder eventuele bestaande tabellen en maakze opnieuw aan.
    connectie, cursor = connect_met_database()
    verwijder_tabellen(cursor)
    maak_tabellen_aan(cursor)


    vegelijking1, vergelijking2 = sorteer_data_collaborative( cursor, 'root')
    data_storten(vergelijking1, vergelijking2, connectie, cursor, "collaborative","product_id","product1","product2", "product3","product4")

    vergelijking3, vergelijking4 = sorteer_data_content(cursor, 'root')
    data_storten(vergelijking3, vergelijking4, connectie, cursor, "content", "product_id", "product1", "product2", "product3", "product4")

    database_sluiten(connectie, cursor)
    eind = time.time()

    print("\n\tHet process is gelukt en heeft, " + str(round(eind - start, 6)) + " seconden geduurd")

    sys.exit(0)


recommendation_engine()
