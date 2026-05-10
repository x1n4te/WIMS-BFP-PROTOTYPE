const REGION_CAR_CITIES: Record<string, string[]> = {
  'Abra': ['Bangued', 'Boliney', 'Bucay', 'Bucloc', 'Daguioman', 'Danglas', 'Dolores', 'La Paz', 'Lacub', 'Lagangilang', 'Lagayan', 'Langiden', 'Licuan Baay', 'Luba', 'Malibcong', 'Manabo', 'Peñarrubia', 'Pidigan', 'Pilar', 'Sallapadan', 'San Isidro', 'San Juan', 'San Quintin', 'Tayum', 'Tineg', 'Tubo', 'Villaviciosa'],
  'Apayao': ['Calanasan', 'Conner', 'Flora', 'Kabugao', 'Luna', 'Pudtol', 'Santa Marcela'],
  'Benguet': ['Atok', 'Baguio City', 'Bakun', 'Bokod', 'Buguias', 'Itogon', 'Kabayan', 'Kapangan', 'Kibungan', 'La Trinidad', 'Mankayan', 'Sablan', 'Tuba', 'Tublay'],
  'Ifugao': ['Aguinaldo', 'Alfonso Lista', 'Asipulo', 'Banaue', 'Hingyon', 'Hungduan', 'Kiangan', 'Lagawe', 'Lamut', 'Mayoyao', 'Tinoc'],
  'Kalinga': ['Balbalan', 'Lubuagan', 'Pasil', 'Pinukpuk', 'Rizal', 'Tanudan', 'Tinglayan', 'Tabuk City'],
  'Mountain Province': ['Barlig', 'Bauko', 'Besao', 'Bontoc', 'Natonin', 'Paracelis', 'Sabangan', 'Sadanga', 'Sagada', 'Tadian'],
  'Baguio City': ['Baguio City'],
};

const REGION_V_CITIES: Record<string, string[]> = {
  'Albay': ['Bacacay', 'Camalig', 'Daraga', 'Guinobatan', 'Jovellar', 'Legazpi City', 'Libon', 'Ligao City', 'Malilipot', 'Malinao', 'Manito', 'Oas', 'Pio Duran', 'Polangui', 'Rapu Rapu', 'Santo Domingo', 'Tabaco City', 'Tiwi'],
  'Camarines Norte': ['Basud', 'Capalonga', 'Daet', 'Jose Panganiban', 'Labo', 'Mercedes', 'Paracale', 'San Lorenzo Ruiz', 'San Vicente', 'Santa Elena', 'Talisay', 'Vinzons'],
  'Camarines Sur': ['Baao', 'Balatan', 'Bato', 'Bombon', 'Buhi', 'Bula', 'Cabusao', 'Calabanga', 'Camaligan', 'Canaman', 'Caramoan', 'Del Gallego', 'Gachitorena', 'Gainza', 'Goa', 'Iriga City', 'Lagonoy', 'Libmanan', 'Lupi', 'Magarao', 'Milaor', 'Minalabac', 'Nabua', 'Naga City', 'Ocampo', 'Pamplona', 'Pasacao', 'Pili', 'Presentacion', 'Ragay', 'Sagnay', 'San Fernando', 'San Jose', 'Sipocot', 'Siruma', 'Tigaon', 'Tinambac'],
  'Catanduanes': ['Bagamanok', 'Baras', 'Bato', 'Caramoran', 'Gigmoto', 'Pandan', 'Panganiban', 'San Andres', 'San Miguel', 'Viga', 'Virac'],
  'Masbate': ['Aroroy', 'Baleno', 'Balud', 'Batuan', 'Cataingan', 'Cawayan', 'Claveria', 'Dimasalang', 'Esperanza', 'Mandaon', 'Masbate City', 'Milagros', 'Mobo', 'Monreal', 'Palanas', 'Pio V Corpuz', 'Placer', 'San Fernando', 'San Jacinto', 'San Pascual', 'Uson'],
  'Sorsogon': ['Barcelona', 'Bulan', 'Bulusan', 'Casiguran', 'Castilla', 'Donsol', 'Gubat', 'Irosin', 'Juban', 'Magallanes', 'Matnog', 'Pilar', 'Prieto Diaz', 'Santa Magdalena', 'Sorsogon City'],
};

const REGION_VI_CITIES: Record<string, string[]> = {
  'Aklan': ['Altavas', 'Balete', 'Banga', 'Batan', 'Buruanga', 'Ibajay', 'Kalibo', 'Lezo', 'Libacao', 'Madalag', 'Makato', 'Malay', 'Malinao', 'Nabas', 'New Washington', 'Numancia', 'Tangalan'],
  'Antique': ['Anini-y', 'Barbaza', 'Belison', 'Bugasong', 'Caluya', 'Culasi', 'Hamtic', 'Laua-an', 'Libertad', 'Pandan', 'Patnongon', 'San Jose', 'San Remigio', 'Sebaste', 'Sibalom', 'Tibiao', 'Tobias Fornier', 'Valderrama'],
  'Capiz': ['Cuartero', 'Dao', 'Dumalag', 'Dumarao', 'Ivisan', 'Jamindan', 'Maayon', 'Mambusao', 'Panay', 'Panitan', 'Pilar', 'Pontevedra', 'President Roxas', 'Roxas City', 'Sapian', 'Sigma', 'Tapaz'],
  'Guimaras': ['Buenavista', 'Jordan', 'Nueva Valencia', 'San Lorenzo', 'Sibunag'],
  'Iloilo': ['Ajuy', 'Alimodian', 'Anilao', 'Badiangan', 'Balasan', 'Banate', 'Barotac Nuevo', 'Barotac Viejo', 'Batad', 'Bingawan', 'Cabatuan', 'Calinog', 'Carles', 'Concepcion', 'Dingle', 'Dueñas', 'Dumangas', 'Estancia', 'Guimbal', 'Igbaras', 'Iloilo City', 'Janiuay', 'Lambunao', 'Leganes', 'Lemery', 'Leon', 'Maasin', 'Miagao', 'Mina', 'New Lucena', 'Oton', 'Passi City', 'Pavia', 'Pototan', 'San Dionisio', 'San Enrique', 'San Joaquin', 'San Miguel', 'San Rafael', 'Sara', 'Santa Barbara', 'Tigbauan', 'Tubungan', 'Zarraga'],
  'Negros Occidental': ['Bacolod City', 'Bago City', 'Binalbagan', 'Cadiz City', 'Calatrava', 'Candoni', 'Cauayan', 'Enrique B Magalona', 'Escalante City', 'Himamaylan City', 'Hinigaran', 'Hinoba', 'Ilog', 'Kabankalan City', 'La Carlota City', 'La Castellana', 'Manapla', 'Moises Padilla', 'Murcia', 'Palupandan', 'Pontevedra', 'Salvador Benedicto', 'Sagay City', 'San Carlos City', 'San Enrique', 'Silay City', 'Sipalay City', 'Talisay City', 'Toboso', 'Valladolid', 'Victorias City'],
};

const REGION_VII_CITIES: Record<string, string[]> = {
  'Bohol': ['Alburquerque', 'Alicia', 'Anda', 'Antequera', 'Baclayon', 'Balilihan', 'Batuan', 'Bien Unido', 'Bilar', 'Buenavista', 'Calape', 'Candijay', 'Pres Carlos P Garcia', 'Carmen', 'Catigbian', 'Clarin', 'Corella', 'Cortes', 'Dagohoy', 'Danao', 'Dauis', 'Dimiao', 'Duero', 'Garcia Hernandez', 'Guindulman', 'Inabanga', 'Jagna', 'Jetafe', 'Lila', 'Loay', 'Loboc', 'Loon', 'Mabini', 'Maribojoc', 'Panglao', 'Pilar', 'Sagbayan', 'San Isidro', 'San Miguel', 'Sevilla', 'Sierra Bullones', 'Sikatuna', 'Tagbilaran', 'Talibon', 'Trinidad', 'Tubigon', 'Ubay', 'Valencia'],
  'Cebu': ['Alcantara', 'Alcoy', 'Alegria', 'Aloguinsan', 'Argao', 'Asturias', 'Badian', 'Balamban', 'Bantayan', 'Barili', 'Bogo City', 'Boljoon', 'Borbon', 'Carcar City', 'Carmen', 'Catmon', 'Cebu City', 'Compostela', 'Consolacion', 'Cordova', 'Daanbantayan', 'Dalaguete', 'Danao City', 'Dumanjug', 'Ginatilan', 'Lapu Lapu City', 'Liloan', 'Madredejos', 'Malabuyoc', 'Mandaue City', 'Medellin', 'Minglanilla', 'Moalboal', 'Naga City', 'Oslob', 'Pilar', 'Pinamungajan', 'Poro', 'Ronda', 'Samboan', 'San Fernando', 'San Francisco', 'San Remegio', 'Santander', 'Sibonga', 'Sogod', 'Sta Fe', 'Tabogon', 'Tabuelan', 'Talisay City', 'Toledo City', 'Tuburan', 'Tudela'],
  'Negros Oriental': ['Amlan', 'Ayungon', 'Bacong', 'Bais City', 'Basay', 'Bayawan City', 'Bindoy', 'Canlaon City', 'Dauin', 'Dumaguete City', 'Guihulngan City', 'Jimalalud', 'La Libertad', 'Mabinay', 'Manjuyod', 'Pamplona', 'San Jose', 'Siaton', 'Sibulan', 'Sta Catalina', 'Tanjay City', 'Tayasan', 'Valencia', 'Vallehermoso', 'Zamboaguita'],
  'Siquijor': ['Enrique Villanueva', 'Larena', 'Lazi', 'Maria', 'San Juan'],
};

const REGION_VIII_CITIES: Record<string, string[]> = {
  'Biliran': ['Almeria', 'Cabucgayan', 'Caibiran', 'Culaba', 'Kawayan', 'Maripipi', 'Naval'],
  'Eastern Samar': ['Arteche', 'Balangiga', 'Balangkayan', 'Borongan City', 'Can-avid', 'Dolores', 'General MacArthur', 'Giporlos', 'Guiuan', 'Hernani', 'Jipapad', 'Lawaan', 'Llorente', 'Maslog', 'Maydolong', 'Mercedes', 'Oras', 'Quinapondan', 'Salcedo', 'San Julian', 'San Policarpo', 'Sulat', 'Taft'],
  'Leyte': ['Abuyog', 'Alang-alang', 'Albuera', 'Babatngon', 'Barugo', 'Bato', 'Baybay City', 'Burauen', 'Calubian', 'Capoocan', 'Carigara', 'Dagami', 'Dulag', 'Hilongos', 'Hindang', 'Inopacan', 'Isabel', 'Jaro', 'Javier', 'Julita', 'Kananga', 'La Paz', 'Leyte', 'MacArthur', 'Mahaplag', 'Matag-ob', 'Matalom', 'Mayorga', 'Merida', 'Ormoc City', 'Palo', 'Palompon', 'Pastrana', 'San Isidro', 'San Miguel', 'Santa Fe', 'Tabango', 'Tabontabon', 'Tacloban City', 'Tanauan', 'Tolosa', 'Tunga', 'Villaba'],
  'Northern Samar': ['Allen', 'Biri', 'Bobon', 'Capul', 'Catarman', 'Catubig', 'Gamay', 'Laoang', 'Lapinig', 'Las Navas', 'Lavezares', 'Lope de Vega', 'Mapanas', 'Mondragon', 'Palapag', 'Pambujan', 'Rosario', 'San Antonio', 'San Isidro', 'San Jose', 'San Roque', 'San Vicente', 'Silvino Lobos', 'Victoria'],
  'Samar': ['Almagro', 'Basey', 'Calbayog City', 'Calbiga', 'Catbalogan', 'Daram', 'Gandara', 'Hinabangan', 'Jiabong', 'Marabut', 'Matuguinao', 'Motiong', 'Pagsanghan', 'Paranas', 'Pinabacdao', 'San Jorge', 'San Jose de Buan', 'San Sebastian', 'Santa Margarita', 'Santa Rita', 'Santo Nino', 'Tagapul', 'Talalora', 'Tarangnan', 'Villareal', 'Zumarraga'],
  'Southern Leyte': ['Anahawan', 'Bontoc', 'Hinunangan', 'Hinundayan', 'Libagon', 'Liloan', 'Limasawa', 'Maasin City', 'Macrohon', 'Malitbog', 'Padre Burgos', 'Pintuyan', 'Saint Bernard', 'San Francisco', 'San Juan', 'San Ricardo', 'Silago', 'Sogod', 'Tomas Oppus'],
};

const REGION_IX_CITIES: Record<string, string[]> = {
  'Zamboanga del Norte': ['Baliquian', 'La Libertad', 'Mutia', 'Sergio Osmena Sr', 'Jose Dalman', 'Gutalac', 'Godod', 'Sirawai', 'Tampilisan', 'Bacungan', 'Kalawit', 'Dapitan City', 'Dipolog City', 'Katipunan', 'Labason', 'Liloy', 'Manukan', 'Pinan', 'Polanco', 'Rizal', 'President Manuel A Roxas', 'Saiyan', 'Salug', 'Sibuco', 'Sibutad', 'Sindangan', 'Siocon'],
  'Zamboanga del Sur': ['Aurora', 'Bayog', 'Dimataling', 'Dinas', 'Dumalinao', 'Dumingag', 'Guipos', 'Josefina', 'Kumalarang', 'Labangan', 'Lakewood', 'Lapuyan', 'Mahayag', 'Margosatubig', 'Midsalip', 'Molave', 'Pagadian City', 'Pitogo', 'Ramon Magasaysay', 'San Miguel', 'San Pablo', 'Sominot', 'Tabina', 'Tambulig', 'Tigbao', 'Tukuran', 'Vincenzo A Sagun', 'Zamboanga City'],
  'Zamboanga Sibugay': ['Buug', 'Imelda', 'Alicia', 'Payao', 'Talusan', 'Naga', 'Roseller T Lim', 'Diplahan', 'Ipil', 'Isabela City', 'Kabasalan', 'Mabuhay', 'Malangas', 'Olutanga', 'Siay', 'Titay', 'Tungawan'],
};

const REGION_X_CITIES: Record<string, string[]> = {
  'Bukidnon': ['Cabanglasan', 'Dangcagan', 'Don Carlos', 'Impasugong', 'Kadingilan', 'Kalilangan', 'Kibawe', 'Lantapan', 'Libona', 'Malaybalay City', 'Malitbog', 'Manolo Fortich', 'Maramag', 'Baungon', 'Damulog', 'Kitaotao', 'Pangantucan', 'Quezon', 'San Fernando', 'Sumilao', 'Talakag', 'Valencia City'],
  'Camiguin': ['Catarman', 'Guinsiliban', 'Mambajao', 'Mahinog', 'Sagay'],
  'Lanao del Norte': ['Bacolod', 'Baloi', 'Matungao', 'Tagoloan', 'Pantar', 'Pantao Ragat', 'Poona Piagapo', 'Baroy', 'Iligan City', 'Kapatagan', 'Kauswagan', 'Kolambogan', 'Lala', 'Linamon', 'Magsaysay', 'Maigo', 'Munai', 'Nunungan', 'Salvador', 'Sapad', 'Sultan Naga Dimaporo', 'Tangkal', 'Tubod'],
  'Misamis Occidental': ['Aloran', 'Baliangao', 'Bonifacio', 'Calamba', 'Clarin', 'Concepcion', 'Don Victoriano Chiongbian', 'Jimenez', 'Lopez Jaena', 'Oroquieta City', 'Ozamiz City', 'Pana-on', 'Plaridel', 'Sapang Dalaga', 'Sinacaban', 'Tangub City', 'Tudela'],
  'Misamis Oriental': ['Alubijid', 'Balingasag', 'Balingoan', 'Binuangan', 'Cagayan De Oro City', 'Claveria', 'El Salvador City', 'Gingoog City', 'Gitagum', 'Initao', 'Jasaan', 'Kinoguitan', 'Lagonglong', 'Laguindingan', 'Libertad', 'Lugait', 'Magsaysay', 'Manticao', 'Medina', 'Naawan', 'Opol', 'Salay', 'Sugbongcogan', 'Tagoloan', 'Talisayan', 'Villanueva'],
};

const REGION_XI_CITIES: Record<string, string[]> = {
  'Davao de Oro': ['Compostela', 'Laak', 'Mabini', 'Maco', 'Maragusan', 'Mawab', 'Monkayo', 'Montevista', 'Nabunturan', 'New Bataan', 'Pantukan'],
  'Davao del Norte': ['Asuncion', 'Carmen', 'Braulio E Dujali', 'Kapalong', 'New Corella', 'Panabo City', 'Samal Island', 'San Isidro', 'Santo Tomas', 'Tagum City', 'Talaingud'],
  'Davao del Sur': ['Bansalan', 'Davao City', 'Digos City', 'Hagonoy', 'Kiblawan', 'Magsaysay', 'Malalag', 'Matanao', 'Padada', 'Santa Cruz', 'Sulop'],
  'Davao Occidental': ['Don Marcelino', 'Jose Abad Santos', 'Malita', 'Santa Maria'],
  'Davao Oriental': ['Baganga', 'Banaybanay', 'Boston', 'Caraga', 'Cateel', 'Governor Generoso', 'Lupon', 'Manay', 'Mati City', 'San Isidro', 'Tarragona'],
};

const REGION_XII_CITIES: Record<string, string[]> = {
  'North Cotabato': ['Alamada', 'Aleosan', 'Antipas', 'Arakan', 'Banisilan', 'Carmen', 'Cotabato City', 'Kabacan', 'Kidapawan City', 'Libungan', 'Magpet', 'Makilala', 'Matalam', 'Midsayap', 'Mlang', 'Pigcawayan', 'Pikit', 'President Roxas', 'Tulunan'],
  'Sarangani': ['Alabel', 'Glan', 'Kiamba', 'Maasim', 'Maitum', 'Malapatan', 'Malungon'],
  'South Cotabato': ['Banga', 'General Santos City', 'Koronadal City', 'Lake Sebu', 'Norala', 'Polomolok', 'Santo Niño', 'Surallah', 'Tampakan', 'Tantangan', 'Tboli', 'Tupi'],
  'Sultan Kudarat': ['Bagumbayan', 'Colombio', 'Esperanza', 'Isulan', 'Kalamansig', 'Lambayong', 'Lebak', 'Lutayan', 'Palimbang', 'President Quirino', 'Senator Ninoy Aquino', 'Tacurong City'],
};

const REGION_XIII_CITIES: Record<string, string[]> = {
  'Agusan del Norte': ['Buenavista', 'Butuan City', 'Cabadbaran City', 'Carmen', 'Jabonga', 'Kitcharao', 'Las Nieves', 'Magallanes', 'Nasipit', 'Remedios T Romualdez', 'Santiago', 'Tubay'],
  'Agusan del Sur': ['Bayugan City', 'Bunawan', 'Esperanza', 'La Paz', 'Loreto', 'Prosperidad', 'Rosario', 'San Francisco', 'San Luis', 'Sibagat', 'Santa Josefa', 'Talacogon', 'Trento', 'Veruela'],
  'Dinagat Islands': ['Basilisa', 'Cagdianao', 'Dinagat', 'Libjo', 'Loreto', 'San Jose', 'Tubajon'],
  'Surigao del Norte': ['Alegria', 'Bacuag', 'Burgos', 'Claver', 'Dapa', 'Del Carmen', 'General Luna', 'Gigaquit', 'Mainit', 'Malimono', 'Pilar', 'Placer', 'San Benito', 'San Francisco', 'San Isidro', 'Sison', 'Socorro', 'Santa Monica', 'Surigao City', 'Tagana', 'Tubod'],
  'Surigao del Sur': ['Barobo', 'Bayabas', 'Bislig City', 'Cagwait', 'Cantilan', 'Carrascal', 'Carmen', 'Cortes', 'Hinatuan', 'Lanuza', 'Lianga', 'Lingig', 'Madrid', 'Marihatag', 'San Agustin', 'San Miguel', 'Tagbina', 'Tago', 'Tandag City'],
};

const BARMM_CITIES: Record<string, string[]> = {
  'Basilan': ['Akbar', 'Al Barka', 'Hadji Mohammad Ajul', 'Hadji Muhtamad', 'Lamitan City', 'Lantawan', 'Maluso', 'Sumisip', 'Tabuan Lasa', 'Tipo Tipo', 'Tuburan', 'Ungkaya Pukan'],
  'Lanao del Sur': ['Bacolod Kalawi', 'Balabagan', 'Balindong', 'Bayang', 'Binidayan', 'Buadiposo Buntong', 'Bubong', 'Bumbaran', 'Butig', 'Calanogas', 'Ditsaan Ramain', 'Ganassi', 'Kapai', 'Kapatagan', 'Lumba Bayabao', 'Lumbaca Unayan', 'Lumbatan', 'Lumbayanague', 'Madalum', 'Madamba', 'Maguing', 'Malabang', 'Marantao', 'Marawi City', 'Marogong', 'Masiu', 'Mulondo', 'Pagayawan', 'Piagapo', 'Picong', 'Poona Bayabao', 'Pualas', 'Saguiaran', 'Sultan Dumalondong', 'Tagoloan II', 'Tamparan', 'Taraka', 'Tubaran', 'Tugaya', 'Wao'],
  'Maguindanao del Norte': ['Ampatuan', 'Barira', 'Buldon', 'Buluan', 'Datu Abdullah Sangki', 'Datu Anggal Midtimbang', 'Datu Blah T Sinsuat', 'Datu Hoffer Ampatuan', 'Datu Montawal', 'Datu Odin Sinsuat', 'Datu Paglas', 'Datu Piang', 'Datu Salibo', 'Datu Saudi Ampatuan', 'Datu Unsay', 'General Salipada K Pendatun', 'Guindulungan', 'Kabuntalan', 'Mamasapano', 'Mangudadatu', 'Matanog', 'Northern Kabuntalan', 'Pagalungan', 'Paglat', 'Pandag', 'Parang', 'Rajah Buayan', 'Shariff Aguak', 'Shariff Saydona Mustapha', 'South Upi', 'Sultan Mastura', 'Sultan sa Barongis', 'Talayan', 'Talitay', 'Upi'],
  'Maguindanao del Sur': ['Ampatuan', 'Barira', 'Buldon', 'Buluan', 'Datu Abdullah Sangki', 'Datu Anggal Midtimbang', 'Datu Blah T Sinsuat', 'Datu Hoffer Ampatuan', 'Datu Montawal', 'Datu Odin Sinsuat', 'Datu Paglas', 'Datu Piang', 'Datu Salibo', 'Datu Saudi Ampatuan', 'Datu Unsay', 'General Salipada K Pendatun', 'Guindulungan', 'Kabuntalan', 'Mamasapano', 'Mangudadatu', 'Matanog', 'Northern Kabuntalan', 'Pagalungan', 'Paglat', 'Pandag', 'Parang', 'Rajah Buayan', 'Shariff Aguak', 'Shariff Saydona Mustapha', 'South Upi', 'Sultan Mastura', 'Sultan sa Barongis', 'Talayan', 'Talitay', 'Upi'],
  'Sulu': ['Banguingui', 'Hadji Panglima Tahil', 'Indanan', 'Jolo', 'Kalingalan Caluang', 'Lugus', 'Luuk', 'Maimbung', 'Old Panamao', 'Omar', 'Pandami', 'Panglima Estino', 'Pangutaran', 'Parang', 'Pata', 'Patikul', 'Siasi', 'Talipao', 'Tapul'],
  'Tawi-Tawi': ['Bongao', 'Languyan', 'Mapun', 'Panglima Sugala', 'Sapa Sapa', 'Sibutu', 'Simunul', 'Sitangkai', 'South Ubian', 'Tandubas', 'Turtle Islands'],
};

const NIR_CITIES: Record<string, string[]> = {
  'Negros Occidental': ['Bacolod City', 'Bago City', 'Binalbagan', 'Cadiz City', 'Calatrava', 'Candoni', 'Cauayan', 'Enrique B Magalona', 'Escalante City', 'Himamaylan City', 'Hinigaran', 'Hinoba', 'Ilog', 'Kabankalan City', 'La Carlota City', 'La Castellana', 'Manapla', 'Moises Padilla', 'Murcia', 'Palupandan', 'Pontevedra', 'Salvador Benedicto', 'Sagay City', 'San Carlos City', 'San Enrique', 'Silay City', 'Sipalay City', 'Talisay City', 'Toboso', 'Valladolid', 'Victorias City'],
  'Negros Oriental': ['Amlan', 'Ayungon', 'Bacong', 'Bais City', 'Basay', 'Bayawan City', 'Bindoy', 'Canlaon City', 'Dauin', 'Dumaguete City', 'Guihulngan City', 'Jimalalud', 'La Libertad', 'Mabinay', 'Manjuyod', 'Pamplona', 'San Jose', 'Siaton', 'Sibulan', 'Sta Catalina', 'Tanjay City', 'Tayasan', 'Valencia', 'Vallehermoso', 'Zamboaguita'],
};
