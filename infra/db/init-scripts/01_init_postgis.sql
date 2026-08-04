-- Script d'initialisation PostGIS
-- Ce script est exécuté au premier démarrage du conteneur

-- Activer l'extension PostGIS (déjà incluse dans l'image postgis/postgis)
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder;

-- Vérification
SELECT PostGIS_Full_Version();
