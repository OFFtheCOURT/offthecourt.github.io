/* ================= Idiomas: español (original), català e English =================
   La web se escribe en español; este módulo traduce lo que se pinta en pantalla:
   - D: frases fijas (texto exacto)          - RX: frases con números o nombres (expresiones regulares)
   - HD: títulos con palabra resaltada        - fechas y horas con el formato del idioma (LOCALE)
   Un MutationObserver traduce todo lo que se añade o cambia en la página. Cambiar de idioma recarga la web. */
const LANGS={es:'Español',ca:'Català',en:'English'};
let LANG=(()=>{try{const s=localStorage.getItem('offcourt-lang');if(s&&LANGS[s])return s}catch(e){}
  const q=new URLSearchParams(location.search).get('lang');if(q&&LANGS[q])return q;
  const n=(navigator.languages||[navigator.language||'es']).map(x=>String(x).toLowerCase());
  for(const x of n){if(x.startsWith('ca'))return 'ca';if(x.startsWith('es')||x.startsWith('gl')||x.startsWith('eu'))return 'es';if(x.startsWith('en'))return 'en'}return 'es'})();
const LOCALE=()=>({es:'es-ES',ca:'ca-ES',en:'en-GB'})[LANG];
document.documentElement.lang=LANG;
// [español, english, català]
const I18N_D=[
// Lo que dejó la noche (curio.py): etiquetas, unidades y líneas
['MÁXIMO DEL AÑO','SEASON HIGH','MÀXIM DE L\'ANY'],['TRIPLE-DOBLE','TRIPLE-DOUBLE','TRIPLE-DOBLE'],['DOBLE-DOBLE','DOUBLE-DOUBLE','DOBLE-DOBLE'],['EN RACHA','ON A ROLL','EN RATXA'],
['MEJOR RACHA','BEST STREAK','MILLOR RATXA'],['EN CAÍDA LIBRE','IN FREE FALL','EN CAIGUDA LLIURE'],['EXHIBICIÓN','SHOWTIME','EXHIBICIÓ'],['PUNTERÍA PERFECTA','PERFECT SHOOTING','PUNTERIA PERFECTA'],
['RÉCORD DE TRIPLES','THREE-POINT RECORD','RÈCORD DE TRIPLES'],['LLUVIA DE TRIPLES','RAINING THREES','PLUJA DE TRIPLES'],['¡POR FIN!','AT LAST!','PER FI!'],['RÉCORD DEL AÑO','SEASON RECORD','RÈCORD DE L\'ANY'],
['PALIZA DEL AÑO','BLOWOUT OF THE YEAR','PALLISSA DE L\'ANY'],['PARTIDAZO','INSTANT CLASSIC','PARTIDÀS'],['FINAL DE INFARTO','THRILLER','FINAL D\'INFART'],
['SEGUIDAS','IN A ROW','SEGUIDES'],['DERROTAS','LOSSES','DERROTES'],['PUNTOS','POINTS','PUNTS'],['VICTORIA','WIN','VICTÒRIA'],['PALIZA','MARGIN','PALLISSA'],['EN TIROS','FG','EN TIRS'],
['PRÓRROGA','OVERTIME','PRÒRROGA'],['PRÓRROGAS','OVERTIMES','PRÒRROGUES'],['AL LÍMITE','TO THE WIRE','AL LÍMIT'],['TRIPLES','THREES','TRIPLES'],
['Partidazo hasta el final','A classic to the very end','Partidàs fins al final'],['Se decidió en la última posesión','Decided on the last possession','Es va decidir en l\'última possessió'],
['La mayor anotación de la temporada','The highest score of the season','La màxima anotació de la temporada'],
['. Fotos de jugadores: Wikimedia Commons, con licencias libres; cuando no hay foto libre se muestran las iniciales.','. Player photos: Wikimedia Commons, under free licences; when there is no free photo, initials are shown.','. Fotos de jugadors: Wikimedia Commons, amb llicències lliures; quan no hi ha foto lliure es mostren les inicials.'],
['Este ·','East ·','Est ·'],['Oeste ·','West ·','Oest ·'],['Idioma','Language','Idioma'],
['Agenda','Schedule','Agenda'],['Calendario','Calendar','Calendari'],['Clasificación','Standings','Classificació'],['Líderes','Leaders','Líders'],
['Líderes individuales','Individual leaders','Líders individuals'],['Estadísticas','Stats','Estadístiques'],['Estadísticas equipos','Team stats','Estadístiques equips'],
['Estadísticas de equipo','Team stats','Estadístiques d\'equip'],['Estadísticas y top 5','Stats & top 5','Estadístiques i top 5'],['Mi equipo','My team','El meu equip'],['★ Mi equipo','★ My team','★ El meu equip'],
['Menú','Menu','Menú'],['Hoy','Today','Avui'],['Esta noche','Tonight','Aquesta nit'],['En directo','Live','En directe'],['Próximos','Upcoming','Propers'],['Próximos partidos','Upcoming games','Propers partits'],
['Por fechas','By date','Per dates'],['Por jornadas','By round','Per jornades'],['Última jornada','Latest round','Última jornada'],['Partido de la jornada','Game of the round','Partit de la jornada'],
['Partido de la noche','Game of the night','Partit de la nit'],['MVP de la jornada','MVP of the round','MVP de la jornada'],['MVP de la noche','MVP of the night','MVP de la nit'],
['¿Qué quieres consultar?','What are you looking for?','Què vols consultar?'],['Promedios por partido','Per-game averages','Mitjanes per partit'],['Ranking','Ranking','Rànquing'],
['Los mejores de la liga en cada estadística.','The league\'s best in every stat.','Els millors de la lliga en cada estadística.'],
['Elige una estadística para ordenar a los equipos.','Pick a stat to rank the teams.','Tria una estadística per ordenar els equips.'],
['Elige un día para ver sus partidos, estadísticas y jugadores destacados.','Pick a day to see its games, stats and top players.','Tria un dia per veure\'n els partits, les estadístiques i els jugadors destacats.'],
['Elige una jornada para ver sus partidos, estadísticas y jugadores destacados.','Pick a round to see its games, stats and top players.','Tria una jornada per veure\'n els partits, les estadístiques i els jugadors destacats.'],
['Horarios en hora de España. Elige la jornada.','Times in Spanish time (CET). Pick the round.','Horaris en hora d\'Espanya. Tria la jornada.'],
['Horarios en hora de España. Elige la noche.','Times in Spanish time (CET). Pick the night.','Horaris en hora d\'Espanya. Tria la nit.'],
['Temporada 2026-27','2026-27 season','Temporada 2026-27'],['Toda la temporada ·','Whole season ·','Tota la temporada ·'],['partidos por jugar','games left','partits per jugar'],
['Equipo','Team','Equip'],['Jugador','Player','Jugador'],['Jugadores','Players','Jugadors'],['Partido','Game','Partit'],['Partidos','Games','Partits'],['partidos','games','partits'],
['Racha','Streak','Ratxa'],['Casa','Home','Casa'],['Fuera','Away','Fora'],['En casa','At home','A casa'],['Local','Home','Local'],['Dif.','Diff.','Dif.'],['Últimos 5 →','Last 5 →','Últims 5 →'],
['Playoffs','Playoffs','Playoffs'],['Play-in','Play-in','Play-in'],['Descenso','Relegation','Descens'],['Desliza para ver más →','Swipe to see more →','Llisca per veure\'n més →'],
['Ver más','See more','Veure\'n més'],['Ver top 10','See top 10','Veure top 10'],['Ver top 5','See top 5','Veure top 5'],['Detalles','Details','Detalls'],['Ficha completa','Box score','Fitxa completa'],
['Ficha en directo','Live box score','Fitxa en directe'],['Ficha completa del partido','Full box score','Fitxa completa del partit'],['▶ Resumen','▶ Highlights','▶ Resum'],['▶ Ver resumen','▶ Watch highlights','▶ Veure resum'],
['● Seguir en directo','● Follow live','● Seguir en directe'],['● En directo','● Live','● En directe'],['● Próximamente','● Coming up','● Properament'],['● Resultados finales','● Final results','● Resultats finals'],['● Terminados','● Finished','● Acabats'],
['Final','Final','Final'],['Prórroga','Overtime','Pròrroga'],['Tiro','Shooting','Tir'],['Puntos por cuarto','Points by quarter','Punts per quart'],['Jugadores más destacados','Top performers','Jugadors més destacats'],
['Jugadas destacadas','Top plays','Jugades destacades'],['Evolución del marcador','Score flow','Evolució del marcador'],['Cambios de líder','Lead changes','Canvis de líder'],['Empates','Ties','Empats'],
['Tiros de campo','Field goals','Tirs de camp'],['Triples','3-pointers','Triples'],['Tiros libres','Free throws','Tirs lliures'],['Rebotes','Rebounds','Rebots'],['Asistencias','Assists','Assistències'],
['Robos','Steals','Robatoris'],['Tapones','Blocks','Taps'],['Pérdidas','Turnovers','Pèrdues'],['Valoración','Efficiency','Valoració'],['Minutos','Minutes','Minuts'],['Puntos','Points','Punts'],
['Faltas recibidas','Fouls drawn','Faltes rebudes'],['Faltas personales','Personal fouls','Faltes personals'],['Rebotes ofensivos','Offensive rebounds','Rebots ofensius'],['Rebotes defensivos','Defensive rebounds','Rebots defensius'],
['Pts. en pintura','Points in paint','Punts a la pintura'],['Contraataque','Fast break','Contraatac'],['Tras pérdida','Off turnovers','Després de pèrdua'],['Máx. ventaja','Biggest lead','Màx. avantatge'],
['Segundas opciones','Second chance','Segones opcions'],['Pts. banquillo','Bench points','Punts banqueta'],['Puntos recibidos','Points allowed','Punts rebuts'],['Diferencial','Point diff.','Diferencial'],
['Triples anotados','3-pointers made','Triples anotats'],['Triples por partido','3-pointers per game','Triples per partit'],['Valoración (PIR)','Efficiency (PIR)','Valoració (PIR)'],['+/- por partido','+/- per game','+/- per partit'],
['% Tiros de campo','FG %','% Tirs de camp'],['% Triples','3P %','% Triples'],['% Tiros libres','FT %','% Tirs lliures'],['Mejor ataque:','Best offence:','Millor atac:'],
['Partidos','Games','Partits'],['Máximo anotador','Top scorer','Màxim anotador'],['Más rebotes','Most rebounds','Més rebots'],['Más asistencias','Most assists','Més assistències'],
['Mejor valoración','Best efficiency','Millor valoració'],['Mayor paliza','Biggest win','Major pallissa'],['Más igualado','Closest game','Més igualat'],
['Lo que dejó la noche','Night\'s talking points','El que va deixar la nit'],['Lo que dejó la jornada','Round\'s talking points','El que va deixar la jornada'],
['Elige tu equipo','Pick your team','Tria el teu equip'],['Elegir equipo','Pick team','Triar equip'],['Elige tu equipo favorito','Pick your favourite team','Tria el teu equip preferit'],['Cambiar','Change','Canviar'],
['Verás sus partidos, su forma y su próximo rival al abrir la web','You\'ll see its games, form and next opponent when you open the site','Veuràs els seus partits, la seva forma i el proper rival en obrir la web'],
['Último partido','Last game','Últim partit'],['Próximo partido','Next game','Proper partit'],['Mejor:','Best:','Millor:'],['Sin partidos recientes','No recent games','Sense partits recents'],['Sin partido programado','No game scheduled','Sense partit programat'],
['Quitar mi equipo','Remove my team','Treure el meu equip'],['Hacer mi equipo','Make it my team','Fer-lo el meu equip'],['🔔 Avisarme de sus partidos','🔔 Notify me of its games','🔔 Avisa\'m dels seus partits'],['🔔 Avisos activados','🔔 Alerts on','🔔 Avisos activats'],
['Titulares','Starters','Titulars'],['Banquillo','Bench','Banqueta'],['Total equipo','Team total','Total equip'],['Porcentaje','Percentage','Percentatge'],['Toca una columna para ordenar ·','Tap a column to sort ·','Toca una columna per ordenar ·'],
['en color','in colour','en color'],['mejor dato del equipo · TC: tiros de campo · T3: triples · TL: tiros libres · RO/RD: rebotes ofensivos/defensivos',': team best · FG: field goals · 3P: threes · FT: free throws · OR/DR: offensive/defensive rebounds',': millor dada de l\'equip · TC: tirs de camp · T3: triples · TL: tirs lliures · RO/RD: rebots ofensius/defensius'],
['· Val: valoración','· Eff: efficiency','· Val: valoració'],['Cargando ficha completa…','Loading box score…','Carregant la fitxa completa…'],['Cargando ficha…','Loading…','Carregant…'],['Cargando plantilla…','Loading roster…','Carregant la plantilla…'],['Cargando comparación…','Loading comparison…','Carregant la comparació…'],
['Ficha no disponible','Box score not available','Fitxa no disponible'],['No se ha podido cargar la ficha de este partido. Prueba de nuevo en un rato.','Couldn\'t load this box score. Try again later.','No s\'ha pogut carregar la fitxa d\'aquest partit. Torna-ho a provar d\'aquí a una estona.'],
['Plantilla','Roster','Plantilla'],['Últimos resultados','Recent results','Últims resultats'],['Puntos a favor','Points for','Punts a favor'],['Puntos en contra','Points against','Punts en contra'],['Diferencia','Point diff.','Diferència'],
['Posición jornada a jornada','Position round by round','Posició jornada a jornada'],['Posición semana a semana','Position week by week','Posició setmana a setmana'],['Aún no hay suficientes jornadas para el gráfico.','Not enough rounds yet for the chart.','Encara no hi ha prou jornades per al gràfic.'],
['No hay partidos programados.','No games scheduled.','No hi ha partits programats.'],['Sin partidos todavía.','No games yet.','Encara no hi ha partits.'],['Sin datos de jugadores.','No player data.','Sense dades de jugadors.'],
['Puntos partido a partido','Points game by game','Punts partit a partit'],['Mejor partido','Best game','Millor partit'],['Mejor partido (pts)','Best game (pts)','Millor partit (pts)'],['Todos sus partidos','All games','Tots els seus partits'],['Res.','Res.','Res.'],
['Comparar','Compare','Comparar'],['Cambiar rival','Change opponent','Canviar rival'],['Copiar enlace','Copy link','Copiar enllaç'],['¡Copiado!','Copied!','Copiat!'],['categorías ganadas','categories won','categories guanyades'],
['No hay datos de este jugador esta temporada.','No data for this player this season.','No hi ha dades d\'aquest jugador aquesta temporada.'],['No hay datos de alguno de los dos jugadores.','No data for one of the players.','No hi ha dades d\'algun dels dos jugadors.'],
['Compartir','Share','Compartir'],['Compartir resultado','Share result','Compartir resultat'],['Post 4:5','Post 4:5','Post 4:5'],['Historia 9:16','Story 9:16','Història 9:16'],['Descargar','Download','Descarregar'],['Publicar','Post','Publicar'],
['Creando la imagen…','Creating image…','Creant la imatge…'],['Para Instagram: descarga la imagen (o pulsa Compartir en el móvil) y súbela como post o historia.','For Instagram: download the image (or tap Share on your phone) and upload it as a post or story.','Per a Instagram: descarrega la imatge (o prem Compartir al mòbil) i puja-la com a post o història.'],
['Escribe para buscar','Type to search','Escriu per cercar'],['Equipos','Teams','Equips'],['Sin resultados','No results','Sense resultats'],['Esc','Esc','Esc'],
['Créditos de las fotos','Photo credits','Crèdits de les fotos'],['· Datos de partidos y estadísticas:','· Game data and stats:','· Dades de partits i estadístiques:'],['· Actualizado:','· Updated:','· Actualitzat:'],
['· Jugadores destacados ordenados por','· Top players ranked by','· Jugadors destacats ordenats per'],['valoración (game score)','game score','valoració (game score)'],['valoración PIR','PIR efficiency','valoració PIR'],['valoración','efficiency','valoració'],
['Partidos anteriores','Earlier games','Partits anteriors'],['Más partidos','More games','Més partits'],['Volver arriba','Back to top','Tornar a dalt'],['Offcourt · volver arriba','Offcourt · back to top','Offcourt · tornar a dalt'],
['Jor.','Rd.','Jor.'],['Jornada','Round','Jornada'],['Terminado · resultado en la próxima actualización','Finished · result in the next update','Acabat · resultat a la propera actualització'],
['Cerrar','Close','Tancar'],['Buscar','Search','Cercar'],['Buscar (tecla /)','Search (/ key)','Cercar (tecla /)'],['Buscar equipos y jugadores','Search teams and players','Cercar equips i jugadors'],['Busca un equipo o un jugador…','Search a team or a player…','Cerca un equip o un jugador…'],
['¿Con quién lo comparas? Escribe un jugador…','Compare with whom? Type a player…','Amb qui el compares? Escriu un jugador…'],['Cambiar a modo claro','Switch to light mode','Canviar a mode clar'],['Cambiar a modo oscuro','Switch to dark mode','Canviar a mode fosc'],['Modo claro / oscuro','Light / dark mode','Mode clar / fosc'],
['Jornada anterior','Previous round','Jornada anterior'],['Jornada siguiente','Next round','Jornada següent'],['Semana anterior','Previous week','Setmana anterior'],['Semana siguiente','Next week','Setmana següent'],
['Marcar como mi equipo','Set as my team','Marcar com el meu equip'],['Del más antiguo al más reciente','Oldest to newest','Del més antic al més recent'],['Diferencia en el marcador minuto a minuto','Score margin minute by minute','Diferència al marcador minut a minut'],
['Evolución de la posición','Position over time','Evolució de la posició'],['Reparto de puntos','Points split','Repartiment de punts'],['Media','Average','Mitjana'],['Liga','League','Lliga'],
['Últimos 5 partidos, del más antiguo (izquierda) al más reciente (derecha)','Last 5 games, oldest (left) to newest (right)','Últims 5 partits, del més antic (esquerra) al més recent (dreta)'],
['Resultados y estadísticas de NBA, EuroLiga y ACB','NBA, EuroLeague and ACB scores and stats','Resultats i estadístiques de l\'NBA, l\'Eurolliga i l\'ACB'],['EuroLiga','EuroLeague','Eurolliga'],['Europa','Europe','Europa'],['EE. UU.','USA','EUA'],
['Fase regular','Regular season','Fase regular'],['Conferencia Este','Eastern Conference','Conferència Est'],['Conferencia Oeste','Western Conference','Conferència Oest'],['Liga Endesa','Liga Endesa','Lliga Endesa'],
['Sin fotos todavía.','No photos yet.','Encara no hi ha fotos.'],['Mano caliente','Hot hand','Mà calenta'],['Favorito','Favourite','Favorit'],['Más/menos','Plus/minus','Més/menys'],
['Las notificaciones están bloqueadas para esta web. Actívalas en los ajustes del navegador (icono del candado junto a la dirección).','Notifications are blocked for this site. Enable them in your browser settings (padlock icon next to the address).','Les notificacions estan bloquejades per a aquesta web. Activa-les a la configuració del navegador (icona del cadenat al costat de l\'adreça).'],
['Idioma','Language','Idioma'],
['FINAL','FINAL','FINAL'],['FINAL · PRÓRROGA','FINAL · OVERTIME','FINAL · PRÒRROGA'],['FINAL · AL LÍMITE','FINAL · DOWN TO THE WIRE','FINAL · AL LÍMIT'],['PRÓRROGA','OVERTIME','PRÒRROGA'],
['★ MVP DEL PARTIDO','★ GAME MVP','★ MVP DEL PARTIT'],['RESULTADOS','RESULTS','RESULTATS'],['MVP DEL PARTIDO','GAME MVP','MVP DEL PARTIT'],
['🔴 ¡Ya ha empezado!','🔴 It\'s started!','🔴 Ja ha començat!'],['🔔 Avisos activados','🔔 Alerts on','🔔 Avisos activats'],['Hoy hay','Game','Avui hi ha'],
// cabeceras de tablas y abreviaturas
['Min','Min','Min'],['Pts','Pts','Pts'],['Reb','Reb','Reb'],['Ast','Ast','Ast'],['TC','FG','TC'],['T3','3P','T3'],['TL','FT','TL'],['RO','OR','RO'],['RD','DR','RD'],['Rob','Stl','Rob'],['Tap','Blk','Tap'],['Pér','TO','Pèr'],['FP','PF','FP'],['Val','Eff','Val'],
['PJ','GP','PJ'],['TC%','FG%','TC%'],['V-D','W-L','V-D'],['PF','PF','PF'],['PC','PA','PC'],['TOTAL','TOTAL','TOTAL'],['PTS','PTS','PTS'],['REB','REB','REB'],['AST','AST','AST'],['VAL','EFF','VAL'],
['V','W','V'],['D','L','D'],['Partido','Game','Partit'],
];
// [expresión regular sobre el texto español, inglés, catalán] ($1, $2… y {t:$1} = traducir esa parte)
const I18N_RX=[
[/^RÉCORD (NBA|EUROLIGA|ACB)$/,'{t:$1} RECORD','RÈCORD {t:$1}'],[/^Última: (\d+-\d+) a (.+)$/,'Last: $1 vs $2','Últim: $1 contra $2'],
[/^(.+) · (\d+) prórrogas$/,'$1 · $2OT','$1 · $2 pròrrogues'],[/^(.+) · prórroga$/,'$1 · OT','$1 · pròrroga'],
[/^Paliza \+(\d+)$/,'Blowout +$1','Pallissa +$1'],[/^Igualado · (\d+)$/,'Close game · $1','Igualat · $1'],
[/^Elige tu equipo de la (NBA|EuroLiga|ACB)$/,'Pick your {t:$1} team','Tria el teu equip de l\'{t:$1}'],
[/^([ABPE]|AP) · (\d+')$/,'{t:$1} · $2','$1 · $2'],[/^(.+) · ([ABPE]|AP)$/,'$1 · {t:$2}','$1 · $2'],
[/^(\d+) partidos$/,'$1 games','$1 partits'],[/^(\d+) partido$/,'$1 game','$1 partit'],[/^(\d+) jugados$/,'$1 played','$1 jugats'],
[/^(\d+) partidos · (\d+) puntos en total · media de ([\d.,]+) por equipo$/,'$1 games · $2 total points · $3 per team','$1 partits · $2 punts en total · mitjana de $3 per equip'],
[/^(\d+) partidos? · primer salto a las (\S+) \(hora de España\) · datos actualizados a las (\S+)$/,'$1 games · first tip-off $2 (Spanish time) · data updated $3','$1 partits · primer salt a les $2 (hora d\'Espanya) · dades actualitzades a les $3'],
[/^(\d+) partidos? · primer salto a las (\S+) \(hora de España\)$/,'$1 games · first tip-off $2 (Spanish time)','$1 partits · primer salt a les $2 (hora d\'Espanya)'],
[/^(\d+) puntos · (\d+) por equipo$/,'$1 points · $2 per team','$1 punts · $2 per equip'],
[/^(.+) por delante$/,'$1 ahead','$1 per davant'],[/^Mejor de (.+)$/,'Top for $1','El millor · $1'],[/^Mejor parcial · (.+)$/,'Best run · $1','Millor parcial · $1'],
[/^Máx\. ventaja (.+)$/,'Biggest lead $1','Màx. avantatge $1'],[/^Comparar con… \((.+)\)$/,'Compare with… ($1)','Comparar amb… ($1)'],
[/^Destacado · (.+) gana a (.+)$/,'Standout · $1 beat $2','Destacat · $1 guanya $2'],[/^Destacado · (.+) cae ante (.+)$/,'Standout · $1 fall to $2','Destacat · $1 cau davant $2'],
[/^MVP de la (jornada|noche) · (.+) gana a (.+)$/,'MVP of the {t:$1} · $2 beat $3','MVP de la {t:$1} · $2 guanya $3'],[/^MVP de la (jornada|noche) · (.+) cae ante (.+)$/,'MVP of the {t:$1} · $2 fall to $3','MVP de la {t:$1} · $2 cau davant $3'],
[/^(.+) encadena (\d+) derrotas seguidas, la peor racha de la liga\.$/,'$1 have lost $2 in a row, the league\'s worst streak.','$1 encadena $2 derrotes seguides, la pitjor ratxa de la lliga.'],
[/^(.+) encadena (\d+) derrotas seguidas\.$/,'$1 have lost $2 in a row.','$1 encadena $2 derrotes seguides.'],
[/^(.+) suma (\d+) victorias seguidas, la mejor racha de la liga\.$/,'$1 have won $2 in a row, the league\'s best streak.','$1 suma $2 victòries seguides, la millor ratxa de la lliga.'],
[/^(.+) suma (\d+) victorias seguidas\.$/,'$1 have won $2 in a row.','$1 suma $2 victòries seguides.'],
[/^(.+) mete (\d+) triples, el máximo de la temporada\.$/,'$1 hits $2 threes, a season high.','$1 fica $2 triples, el màxim de la temporada.'],[/^(.+) mete (\d+) triples\.$/,'$1 hits $2 threes.','$1 fica $2 triples.'],
[/^(.+) \((.+)\) hace su mejor marca del año: (\d+) puntos\.$/,'$1 ($2) sets a season high: $3 points.','$1 ($2) fa la seva millor marca de l\'any: $3 punts.'],
[/^(.+) \((.+)\) hace su mejor marca del año: (\d+) rebotes\.$/,'$1 ($2) sets a season high: $3 rebounds.','$1 ($2) fa la seva millor marca de l\'any: $3 rebots.'],
[/^(.+) \((.+)\) hace su mejor marca del año: (\d+) asistencias\.$/,'$1 ($2) sets a season high: $3 assists.','$1 ($2) fa la seva millor marca de l\'any: $3 assistències.'],
[/^(.+) \((.+)\) hace su mejor marca del año: (\d+) de valoración\.$/,'$1 ($2) sets a season high: $3 efficiency.','$1 ($2) fa la seva millor marca de l\'any: $3 de valoració.'],
[/^Doble-doble enorme de (.+): (\d+) puntos y (\d+) rebotes\.$/,'Huge double-double for $1: $2 points and $3 rebounds.','Doble-doble enorme de $1: $2 punts i $3 rebots.'],
[/^¡Por fin! Primera victoria de la temporada para (.+)\.$/,'At last! First win of the season for $1.','Per fi! Primera victòria de la temporada per a $1.'],
[/^Triple-doble de (.+): (\d+) puntos, (\d+) rebotes y (\d+) asistencias, el primero de su temporada\.$/,'Triple-double for $1: $2 points, $3 rebounds and $4 assists, his first this season.','Triple-doble de $1: $2 punts, $3 rebots i $4 assistències, el primer de la seva temporada.'],
[/^Triple-doble de (.+): (\d+) puntos, (\d+) rebotes y (\d+) asistencias \(el (\d+)º de su temporada\)\.$/,'Triple-double for $1: $2 points, $3 rebounds and $4 assists (no. $5 this season).','Triple-doble de $1: $2 punts, $3 rebots i $4 assistències (el $5è de la temporada).'],
[/^Puntería perfecta de (.+): (\d+) de (\d+) en tiros de campo\.$/,'Perfect shooting from $1: $2 of $3 from the field.','Punteria perfecta de $1: $2 de $3 en tirs de camp.'],
[/^(.+) firma (\d+) (puntos|rebotes|asistencias|de valoración): el récord de la temporada en la (.+)\.$/,'$1 posts $2 {t:$3}: the season record in the {t:$4}.','$1 signa $2 {t:$3}: el rècord de la temporada a la {t:$4}.'],
[/^(.+) anota (\d+) puntos, la mayor anotación de la temporada\.$/,'$1 score $2 points, the season\'s highest.','$1 anota $2 punts, la màxima anotació de la temporada.'],
[/^La mayor paliza del año: (.+) gana de (\d+) a (.+)\.$/,'Biggest win of the year: $1 beat $3 by $2.','La major pallissa de l\'any: $1 guanya de $2 $3.'],
[/^Empieza en (\d+) h (\d+) min$/,'Starts in $1 h $2 min','Comença d\'aquí a $1 h $2 min'],[/^Empieza en (\d+) h$/,'Starts in $1 h','Comença d\'aquí a $1 h'],[/^Empieza en (\d+) min$/,'Starts in $1 min','Comença d\'aquí a $1 min'],
[/^Final · (.+)$/,'Final · $1','Final · $1'],[/^● (\d+) en directo$/,'● $1 live','● $1 en directe'],
[/^Jornada (\d+) · (\d+) de (\d+) jugados$/,'Round $1 · $2 of $3 played','Jornada $1 · $2 de $3 jugats'],[/^Jornada (\d+) de (\d+) · (.+) · (\d+) partidos$/,'Round $1 of $2 · $3 · $4 games','Jornada $1 de $2 · $3 · $4 partits'],
[/^Jornada (\d+) · (\d+) partidos$/,'Round $1 · $2 games','Jornada $1 · $2 partits'],[/^Jornada (\d+) · (.+)$/,'Round $1 · $2','Jornada $1 · $2'],[/^Jornada (\d+)$/,'Round $1','Jornada $1'],[/^J(\d+)$/,'R$1','J$1'],
[/^Ver (\d+) (días|jornadas) anteriores$/,'See $1 earlier {t:$2}','Veure $1 {t:$2} anteriors'],[/^Ocultar (días|jornadas) anteriores$/,'Hide earlier {t:$1}','Amagar {t:$1} anteriors'],
[/^Ranking de los (\d+) equipos$/,'Ranking of the $1 teams','Rànquing dels $1 equips'],[/^Equipos de la (.+)$/,'{t:$1} teams','Equips de la {t:$1}'],
[/^Del (\d+) al (\d+) entran directos a playoffs; del (\d+) al (\d+) juegan el play-in\.$/,'$1 to $2 go straight to the playoffs; $3 to $4 play the play-in.','Del $1 al $2 van directes als playoffs; del $3 al $4 juguen el play-in.'],
[/^Del (\d+) al (\d+) juegan los playoffs por el título; los (\d+) últimos descienden\.$/,'$1 to $2 play the title playoffs; the bottom $3 are relegated.','Del $1 al $2 juguen els playoffs pel títol; els $3 últims baixen.'],
[/^(\d+)º de la liga$/,'#$1 in the league','$1º de la lliga'],[/^(\d+) ofe\.$/,'$1 off.','$1 ofe.'],[/^(\d+) p\.$/,'$1 g.','$1 p.'],[/^(\d+) prórrogas$/,'$1 overtimes','$1 pròrrogues'],
[/^Medias por partido de la temporada \((.+)\)\. Toca un jugador para ver su ficha\.$/,'Season per-game averages ({t:$1}). Tap a player to open their profile.','Mitjanes per partit de la temporada ({t:$1}). Toca un jugador per veure\'n la fitxa.'],
[/^Ficha completa · (.+)$/,'Box score · $1','Fitxa completa · $1'],[/^Sin resultados para «(.+)»$/,'No results for «$1»','Sense resultats per a «$1»'],
[/^Avisos de los partidos de (.+)$/,'Alerts for $1 games','Avisos dels partits de $1'],[/^Ordenar por (.+)$/,'Sort by {t:$1}','Ordenar per {t:$1}'],[/^Mano caliente: (\d+) puntos$/,'Hot hand: $1 points','Mà calenta: $1 punts'],
[/^Foto: (.+)$/,'Photo: $1','Foto: $1'],[/^Favorito (.+)$/,'Favourite $1','Favorit $1'],[/^Estadísticas de (.+)$/,'{t:$1} stats','Estadístiques de $1'],
[/^(.+) · (\d+) partidos · horario de España$/,'$1 · $2 games · Spanish time','$1 · $2 partits · horari d\'Espanya'],[/^\(fecha de EE\. UU\.\)$/,'(US date)','(data dels EUA)'],[/\(EE\. UU\.\)$/,'(US)','(EUA)'],
[/^Esta noche (.+) · (\d+) partidos$/,'Tonight $1 · $2 games','Aquesta nit $1 · $2 partits'],[/^Mejor: (.+)$/,'Best: $1','Millor: $1'],
[/^FINAL · PALIZA \+(\d+)$/,'FINAL · BLOWOUT +$1','FINAL · PALLISSA +$1'],[/^FINAL · (\d+) PRÓRROGAS$/,'FINAL · $1 OVERTIMES','FINAL · $1 PRÒRROGUES'],[/^(\d+) PRÓRROGAS$/,'$1 OVERTIMES','$1 PRÒRROGUES'],
[/^MEJOR DE (.+)$/,'BEST · $1','MILLOR DE $1'],[/^🏀 Empieza en (\d+) min$/,'🏀 Starts in $1 min','🏀 Comença d\'aquí a $1 min'],
[/^✅ Victoria de (.+)$/,'✅ $1 win','✅ Victòria de $1'],[/^❌ Derrota de (.+)$/,'❌ $1 loss','❌ Derrota de $1'],
[/^(.+) · síguelo en Offcourt$/,'$1 · follow it on Offcourt','$1 · segueix-lo a Offcourt'],[/^(.+) · toca para ver las estadísticas$/,'$1 · tap to see the stats','$1 · toca per veure les estadístiques'],
[/^Te avisaremos antes, al empezar y al terminar cada partido de (.+)\.$/,'We\'ll notify you before, at tip-off and at the end of every $1 game.','T\'avisarem abans, en començar i en acabar cada partit de $1.'],[/^vs (.+)$/,'vs $1','vs $1'],
];
I18N_RX.push(
[/^(#?\d+|\S+) · (Base|Escolta|Alero|Ala-pívot|Pívot)$/,'$1 · {t:$2}','$1 · {t:$2}'],
[/^(\d)C$/,'Q$1','$1Q'],[/^PR(\d)$/,'OT$1','PR$1'],[/^\+(\d+) más$/,'+$1 more','+$1 més'],[/^(\d+) (días|jornadas)$/,'$1 {t:$2}','$1 {t:$2}'],
[/^(.+) · (\d+) partidos$/,'$1 · $2 games','$1 · $2 partits'],[/^(.+) · Top (\d+)$/,'$1 · Top $2','$1 · Top $2']);
I18N_D.push(['Base','Point guard','Base'],['Escolta','Shooting guard','Escorta'],['Alero','Forward','Aler'],['Ala-pívot','Power forward','Ala-pivot'],['Pívot','Center','Pivot'],
 ['% Tiros de 2','2P %','% Tirs de 2'],['Tiros de campo (anotados-intentados)','Field goals (made-attempted)','Tirs de camp (anotats-intentats)'],['· resultados y resúmenes','· results and highlights','· resultats i resums'],
 ['Últimas','Last','Últimes'],['Últimos','Last','Últims'],['con partido','with games','amb partit'],['puntos','points','punts'],['rebotes','rebounds','rebots'],['asistencias','assists','assistències'],
 ['valoración (pir)','efficiency (PIR)','valoració (PIR)'],['robos','steals','robatoris'],['tapones','blocks','taps'],['triples','3-pointers','triples'],['Sin partidos','No games','Sense partits'],['jornada','round','jornada'],['Anoche','Last night','Ahir a la nit'],['Este','East','Est'],['Oeste','West','Oest'],['PR','OT','PR'],['noche','night','nit'],['jornadas','rounds','jornades'],['días','days','dies'],['Mejor ataque:','Best offence:','Millor atac:']);
// pasada final sobre cualquier texto: días, meses y fechas que llegan escritos en español desde los datos
const I18N_POST={
 en:[[/(\d+)º/g,(m,n)=>{n=+n;const t=n%100;return n+((t>10&&t<14)?'th':({1:'st',2:'nd',3:'rd'})[n%10]||'th')}],[/\(fecha de EE\. UU\.\)/g,'(US date)'],[/horario de España/g,'Spanish time'],[/ a las /g,' at '],[/\b(\d{1,2}) de (enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)(?: de (\d{4}))?/gi,(m,d,mo,y)=>`${d} ${({enero:'January',febrero:'February',marzo:'March',abril:'April',mayo:'May',junio:'June',julio:'July',agosto:'August',septiembre:'September',octubre:'October',noviembre:'November',diciembre:'December'})[mo.toLowerCase()]}${y?' '+y:''}`],
   [/\b(Lunes|Martes|Miércoles|Jueves|Viernes|Sábado|Domingo)\b/g,m=>({Lunes:'Monday',Martes:'Tuesday','Miércoles':'Wednesday',Jueves:'Thursday',Viernes:'Friday','Sábado':'Saturday',Domingo:'Sunday'})[m]],
   [/\b(lunes|martes|miércoles|jueves|viernes|sábado|domingo)\b/g,m=>({lunes:'Monday',martes:'Tuesday','miércoles':'Wednesday',jueves:'Thursday',viernes:'Friday','sábado':'Saturday',domingo:'Sunday'})[m]],
   [/\b(lun|mié|jue|vie|sáb|dom)\b/g,m=>({lun:'Mon','mié':'Wed',jue:'Thu',vie:'Fri','sáb':'Sat',dom:'Sun'})[m]],
   [/\b(\d{1,2})(?:-(\d{1,2}))? (ene|feb|abr|may|jun|jul|ago|sept|oct|nov|dic)\b/g,(m,a,b,mo)=>`${a}${b?'-'+b:''} ${({ene:'Jan',feb:'Feb',abr:'Apr',may:'May',jun:'Jun',jul:'Jul',ago:'Aug',sept:'Sep',oct:'Oct',nov:'Nov',dic:'Dec'})[mo]}`]],
 ca:[[/(\d+)º/g,(m,n)=>n+(({1:'r',2:'n',3:'r',4:'t'})[+n]||'è')],[/\(fecha de EE\. UU\.\)/g,'(data dels EUA)'],[/horario de España/g,'horari d\'Espanya'],[/ a las /g,' a les '],[/\b(\d{1,2}) de (enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)(?: de (\d{4}))?/gi,(m,d,mo,y)=>{const n=({enero:'gener',febrero:'febrer',marzo:'març',abril:'abril',mayo:'maig',junio:'juny',julio:'juliol',agosto:'agost',septiembre:'setembre',octubre:'octubre',noviembre:'novembre',diciembre:'desembre'})[mo.toLowerCase()];return `${d} ${/^[ao]/.test(n)?"d'":'de '}${n}${y?' de '+y:''}`}],
   [/\b(Lunes|Martes|Miércoles|Jueves|Viernes|Sábado|Domingo)\b/g,m=>({Lunes:'Dilluns',Martes:'Dimarts','Miércoles':'Dimecres',Jueves:'Dijous',Viernes:'Divendres','Sábado':'Dissabte',Domingo:'Diumenge'})[m]],
   [/\b(lunes|martes|miércoles|jueves|viernes|sábado|domingo)\b/g,m=>({lunes:'dilluns',martes:'dimarts','miércoles':'dimecres',jueves:'dijous',viernes:'divendres','sábado':'dissabte',domingo:'diumenge'})[m]],
   [/\b(lun|mié|jue|vie|sáb|dom)\b/g,m=>({lun:'dl.','mié':'dc.',jue:'dj.',vie:'dv.','sáb':'ds.',dom:'dg.'})[m]],
   [/\b(\d{1,2})(?:-(\d{1,2}))? (ene|feb|abr|may|jun|jul|ago|sept|oct|nov|dic)\b(?!\.)/g,(m,a,b,mo)=>`${a}${b?'-'+b:''} ${({ene:'gen.',feb:'febr.',abr:'abr.',may:'maig',jun:'juny',jul:'jul.',ago:'ag.',sept:'set.',oct:'oct.',nov:'nov.',dic:'des.'})[mo]}`]]};
const I18N_H={ // títulos con palabra resaltada: texto español completo → HTML traducido
 'Partidos de la noche':['Last <span class="hl">night</span>','Partits de la <span class="hl">nit</span>'],'Esta noche se juega':['Tonight\'s <span class="hl">games</span>','Aquesta nit es <span class="hl">juga</span>'],
 'Hoy se juega':['Games <span class="hl">today</span>','Avui es <span class="hl">juga</span>'],'Hoy hay jornada':['Game <span class="hl">day</span>','Avui hi ha <span class="hl">jornada</span>'],
 'Jornada en juego':['Round <span class="hl">in play</span>','Jornada <span class="hl">en joc</span>'],'Última jornada':['Latest <span class="hl">round</span>','Última <span class="hl">jornada</span>'],
 'Partidos por fechas':['Games by <span class="hl">date</span>','Partits per <span class="hl">dates</span>'],'Partidos por jornadas':['Games by <span class="hl">round</span>','Partits per <span class="hl">jornades</span>'],
 'Clasificación':['<span class="hl">Standings</span>','<span class="hl">Classificació</span>'],'Calendario completo':['Full <span class="hl">calendar</span>','Calendari <span class="hl">complet</span>'],
 'Estadísticas de equipos':['Team <span class="hl">stats</span>','Estadístiques d\'<span class="hl">equips</span>'],'Líderes individuales':['Individual <span class="hl">leaders</span>','Líders <span class="hl">individuals</span>'],
 'Próximos partidos':['Upcoming <span class="hl">games</span>','Propers <span class="hl">partits</span>'],
};
const I18N_TOK={es:{},en:{A:'F',B:'G',P:'C',E:'G',AP:'PF',EUROLIGA:'EUROLEAGUE',jornada:'round',noche:'night','días':'days',jornadas:'rounds',NBA:'NBA',EuroLiga:'EuroLeague',ACB:'ACB',puntos:'points',rebotes:'rebounds',asistencias:'assists','de valoración':'efficiency'},
  ca:{EUROLIGA:'EUROLLIGA',jornada:'jornada',noche:'nit','días':'dies',jornadas:'jornades',NBA:'NBA',EuroLiga:'Eurolliga',ACB:'ACB',puntos:'punts',rebotes:'rebots',asistencias:'assistències','de valoración':'de valoració'}};
const I18N_MAP=(()=>{const m={};if(LANG==='es')return m;const k=LANG==='en'?1:2;I18N_D.forEach(r=>{m[r[0]]=r[k]});return m})();
function tr(s){
  if(LANG==='es'||!s)return s;const raw=String(s),t=raw.trim();if(!t)return raw;
  const lead=raw.slice(0,raw.indexOf(t)),tail=raw.slice(raw.indexOf(t)+t.length);
  if(I18N_MAP[t]!==undefined)return lead+I18N_MAP[t]+tail;
  const k0=LANG==='en'?1:2;
  const k=LANG==='en'?1:2;
  for(const r of I18N_RX){const m=t.match(r[0]);if(m){let o=r[k].replace(/\{t:\$(\d)\}/g,(_,i)=>{const v=m[i]||'';return I18N_TOK[LANG][v]||I18N_MAP[v]||v}).replace(/\$(\d)/g,(_,i)=>m[i]||'');return i18nPost(lead+o+tail)}}
  return i18nPost(raw);
}
function i18nPost(s){const P=I18N_POST[LANG];if(!P||!/[a-záéíóúº]/i.test(s))return s;for(const [r,f] of P)s=s.replace(r,f);return s}
const I18N_DONE=new WeakMap();  // texto que ya hemos traducido: no se vuelve a pasar (evita bucles)
function i18nNode(root){
  if(LANG==='es')return;
  const els=root.nodeType===1?[root,...root.querySelectorAll('h1,h2')]:[];
  els.forEach(e=>{if(!/^H[12]$/.test(e.tagName)||!e.querySelector('.hl'))return;const key=e.textContent.replace(/\s+/g,' ').trim(),h=I18N_H[key];if(h){const v=h[LANG==='en'?0:1];if(e.innerHTML!==v)e.innerHTML=v}});
  const w=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);let n;const todo=[];
  if(root.nodeType===3)todo.push(root);else while(n=w.nextNode())todo.push(n);
  for(const x of todo){if(x.parentElement&&x.parentElement.closest('script,style,.no-tr'))continue;if(I18N_DONE.get(x)===x.nodeValue)continue;const v=tr(x.nodeValue);if(v!==x.nodeValue)x.nodeValue=v;I18N_DONE.set(x,x.nodeValue)}
  if(root.nodeType===1)[root,...root.querySelectorAll('[title],[aria-label],[placeholder]')].forEach(e=>{for(const a of ['title','aria-label','placeholder']){const v=e.getAttribute&&e.getAttribute(a);if(v){const t=tr(v);if(t!==v)e.setAttribute(a,t)}}});
}
function i18nStart(){
  if(LANG==='es')return;i18nNode(document.body);
  let q=new Set(),raf=0;new MutationObserver(ms=>{for(const m of ms){if(m.type==='characterData')q.add(m.target);else m.addedNodes.forEach(n=>q.add(n));if(m.type==='attributes')q.add(m.target)}
    if(!raf)raf=requestAnimationFrame(()=>{raf=0;const t=q;q=new Set();t.forEach(n=>{if(n.isConnected)i18nNode(n)})})}).observe(document.body,{childList:true,subtree:true,characterData:true,attributes:true,attributeFilter:['title','aria-label','placeholder']});
}
function setLang(l){if(!LANGS[l])return;try{localStorage.setItem('offcourt-lang',l)}catch(e){}try{track('idioma/'+l,'Idioma: '+l)}catch(e){}location.reload()}
