#!/bin/bash

cd /home/mediadream4/kometa-config

# Reiniciar Kometa
sudo docker stop kometa
sudo docker start kometa
sleep 5

# Ejecutar cambio para Peliculas
sudo docker exec -it kometa python3 -c "from plexapi.server import PlexServer; p=PlexServer('http://172.17.0.1:32400','m4z44etZDM5-dbxabMrK'); movies=p.library.section('Movies').all(); print(f'--- Buscando en {len(movies)} peliculas ---'); [print(f'CAMBIANDO: {m.title}') or m.editAdvanced(languageOverride='es-ES') for m in movies if any('spanish-movies' in str(loc).lower() for loc in m.locations)]"

# Reiniciar Kometa
sudo docker stop kometa
sudo docker start kometa
sleep 5

# Ejecutar cambio para Series
sudo docker exec -it kometa python3 -c "from plexapi.server import PlexServer; p=PlexServer('http://172.17.0.1:32400','m4z44etZDM5-dbxabMrK'); shows=p.library.section('Shows').all(); print(f'--- Analizando {len(shows)} series ---'); [print(f'CAMBIANDO SERIE: {s.title}') or s.editAdvanced(languageOverride='es-ES') for s in shows if any('spanish-shows' in str(loc).lower() for ep in s.episodes() for loc in ep.locations)]"

echo "Cambio de idioma completado: $(date)" >> ~/plex-auto-language.log
