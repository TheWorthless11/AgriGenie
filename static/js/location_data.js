/**
 * Cascading Country → State/Division → District/City dropdown data
 * Used by farmer_onboarding.html and buyer_onboarding.html
 */
const LOCATION_DATA = {
  "Bangladesh": {
    "Barishal": ["Barguna","Barishal","Bhola","Jhalokati","Patuakhali","Pirojpur"],
    "Chattogram": ["Bandarban","Brahmanbaria","Chandpur","Chattogram","Comilla","Cox's Bazar","Feni","Khagrachhari","Lakshmipur","Noakhali","Rangamati"],
    "Dhaka": ["Dhaka","Faridpur","Gazipur","Gopalganj","Kishoreganj","Madaripur","Manikganj","Munshiganj","Narayanganj","Narsingdi","Rajbari","Shariatpur","Tangail"],
    "Khulna": ["Bagerhat","Chuadanga","Jessore","Jhenaidah","Khulna","Kushtia","Magura","Meherpur","Narail","Satkhira"],
    "Mymensingh": ["Jamalpur","Mymensingh","Netrokona","Sherpur"],
    "Rajshahi": ["Bogura","Chapainawabganj","Joypurhat","Naogaon","Natore","Nawabganj","Pabna","Rajshahi","Sirajganj"],
    "Rangpur": ["Dinajpur","Gaibandha","Kurigram","Lalmonirhat","Nilphamari","Panchagarh","Rangpur","Thakurgaon"],
    "Sylhet": ["Habiganj","Moulvibazar","Sunamganj","Sylhet"]
  },
  "India": {
    "Andhra Pradesh": ["Anantapur","Chittoor","East Godavari","Guntur","Krishna","Kurnool","Nellore","Prakasam","Srikakulam","Visakhapatnam","Vizianagaram","West Godavari","YSR Kadapa"],
    "Arunachal Pradesh": ["Itanagar","Tawang","Ziro","Pasighat","Bomdila"],
    "Assam": ["Barpeta","Cachar","Darrang","Dhubri","Dibrugarh","Guwahati","Jorhat","Kamrup","Nagaon","Sivasagar","Sonitpur","Tinsukia"],
    "Bihar": ["Araria","Aurangabad","Bhagalpur","Gaya","Muzaffarpur","Nalanda","Patna","Purnia","Samastipur","Saran","Vaishali"],
    "Chhattisgarh": ["Bastar","Bilaspur","Durg","Korba","Raigarh","Raipur","Rajnandgaon"],
    "Goa": ["North Goa","South Goa"],
    "Gujarat": ["Ahmedabad","Amreli","Anand","Bhavnagar","Gandhinagar","Jamnagar","Junagadh","Kutch","Mehsana","Rajkot","Surat","Vadodara"],
    "Haryana": ["Ambala","Faridabad","Gurugram","Hisar","Karnal","Kurukshetra","Panipat","Rohtak","Sonipat","Yamunanagar"],
    "Himachal Pradesh": ["Bilaspur","Chamba","Hamirpur","Kangra","Kullu","Mandi","Shimla","Sirmaur","Solan","Una"],
    "Jharkhand": ["Bokaro","Deoghar","Dhanbad","Dumka","East Singhbhum","Giridih","Hazaribagh","Ranchi","West Singhbhum"],
    "Karnataka": ["Bagalkot","Ballari","Bangalore Rural","Bangalore Urban","Belagavi","Bidar","Dakshina Kannada","Davangere","Dharwad","Hassan","Mandya","Mysuru","Raichur","Tumkur","Udupi"],
    "Kerala": ["Alappuzha","Ernakulam","Idukki","Kannur","Kasaragod","Kollam","Kottayam","Kozhikode","Malappuram","Palakkad","Pathanamthitta","Thiruvananthapuram","Thrissur","Wayanad"],
    "Madhya Pradesh": ["Bhopal","Gwalior","Indore","Jabalpur","Rewa","Sagar","Satna","Ujjain"],
    "Maharashtra": ["Ahmednagar","Aurangabad","Kolhapur","Mumbai City","Mumbai Suburban","Nagpur","Nashik","Pune","Raigad","Satara","Solapur","Thane"],
    "Manipur": ["Bishnupur","Churachandpur","Imphal East","Imphal West","Thoubal"],
    "Meghalaya": ["East Garo Hills","East Khasi Hills","Ri-Bhoi","Shillong","West Garo Hills"],
    "Mizoram": ["Aizawl","Champhai","Kolasib","Lunglei","Serchhip"],
    "Nagaland": ["Dimapur","Kohima","Mokokchung","Tuensang","Wokha"],
    "Odisha": ["Balasore","Cuttack","Ganjam","Khurda","Koraput","Mayurbhanj","Puri","Sambalpur","Sundargarh"],
    "Punjab": ["Amritsar","Bathinda","Faridkot","Gurdaspur","Jalandhar","Ludhiana","Mohali","Muktsar","Patiala","Sangrur"],
    "Rajasthan": ["Ajmer","Alwar","Bikaner","Jaipur","Jodhpur","Kota","Sikar","Udaipur"],
    "Sikkim": ["East Sikkim","North Sikkim","South Sikkim","West Sikkim"],
    "Tamil Nadu": ["Chennai","Coimbatore","Cuddalore","Erode","Kanchipuram","Madurai","Nagapattinam","Salem","Thanjavur","Tiruchirappalli","Tirunelveli","Vellore"],
    "Telangana": ["Adilabad","Hyderabad","Karimnagar","Khammam","Mahabubnagar","Medak","Nalgonda","Nizamabad","Rangareddy","Warangal"],
    "Tripura": ["Dhalai","Gomati","North Tripura","Sepahijala","South Tripura","West Tripura"],
    "Uttar Pradesh": ["Agra","Aligarh","Allahabad","Bareilly","Ghaziabad","Gorakhpur","Kanpur","Lucknow","Mathura","Meerut","Moradabad","Noida","Varanasi"],
    "Uttarakhand": ["Almora","Dehradun","Haridwar","Nainital","Pauri Garhwal","Udham Singh Nagar"],
    "West Bengal": ["Bankura","Bardhaman","Birbhum","Darjeeling","Hooghly","Howrah","Jalpaiguri","Kolkata","Malda","Medinipur","Murshidabad","Nadia","North 24 Parganas","South 24 Parganas"],
    "Delhi": ["Central Delhi","East Delhi","New Delhi","North Delhi","South Delhi","West Delhi"],
    "Jammu & Kashmir": ["Anantnag","Baramulla","Jammu","Kathua","Srinagar","Udhampur"],
    "Ladakh": ["Kargil","Leh"]
  },
  "Pakistan": {
    "Balochistan": ["Gwadar","Khuzdar","Lasbela","Quetta","Turbat","Zhob"],
    "Khyber Pakhtunkhwa": ["Abbottabad","Bannu","Dera Ismail Khan","Kohat","Mardan","Peshawar","Swabi","Swat"],
    "Punjab": ["Bahawalpur","Dera Ghazi Khan","Faisalabad","Gujranwala","Gujrat","Lahore","Multan","Rawalpindi","Sahiwal","Sargodha","Sialkot"],
    "Sindh": ["Hyderabad","Karachi","Larkana","Mirpur Khas","Nawabshah","Sukkur","Thatta"],
    "Azad Jammu & Kashmir": ["Bagh","Bhimber","Kotli","Mirpur","Muzaffarabad","Rawalakot"],
    "Gilgit-Baltistan": ["Ghizer","Gilgit","Hunza","Skardu"],
    "Islamabad": ["Islamabad"]
  },
  "Nepal": {
    "Province No. 1": ["Bhojpur","Dhankuta","Ilam","Jhapa","Morang","Okhaldhunga","Panchthar","Sankhuwasabha","Solukhumbu","Sunsari","Taplejung","Terhathum","Udayapur"],
    "Madhesh Province": ["Bara","Dhanusha","Mahottari","Parsa","Rautahat","Saptari","Sarlahi","Siraha"],
    "Bagmati Province": ["Bhaktapur","Chitwan","Dhading","Dolakha","Kathmandu","Kavrepalanchok","Lalitpur","Makwanpur","Nuwakot","Ramechhap","Rasuwa","Sindhuli","Sindhupalchok"],
    "Gandaki Province": ["Baglung","Gorkha","Kaski","Lamjung","Manang","Mustang","Myagdi","Nawalpur","Parbat","Syangja","Tanahun"],
    "Lumbini Province": ["Arghakhanchi","Banke","Bardiya","Dang","Gulmi","Kapilvastu","Nawalparasi West","Palpa","Pyuthan","Rolpa","Rupandehi","Rukum East"],
    "Karnali Province": ["Dailekh","Dolpa","Humla","Jajarkot","Jumla","Kalikot","Mugu","Rukum West","Salyan","Surkhet"],
    "Sudurpashchim Province": ["Achham","Baitadi","Bajhang","Bajura","Dadeldhura","Darchula","Doti","Kailali","Kanchanpur"]
  },
  "Sri Lanka": {
    "Central": ["Kandy","Matale","Nuwara Eliya"],
    "Eastern": ["Ampara","Batticaloa","Trincomalee"],
    "North Central": ["Anuradhapura","Polonnaruwa"],
    "Northern": ["Jaffna","Kilinochchi","Mannar","Mullaitivu","Vavuniya"],
    "North Western": ["Kurunegala","Puttalam"],
    "Sabaragamuwa": ["Kegalle","Ratnapura"],
    "Southern": ["Galle","Hambantota","Matara"],
    "Uva": ["Badulla","Moneragala"],
    "Western": ["Colombo","Gampaha","Kalutara"]
  },
  "Malaysia": {
    "Johor": ["Batu Pahat","Johor Bahru","Kluang","Kota Tinggi","Mersing","Muar","Pontian","Segamat"],
    "Kedah": ["Alor Setar","Kulim","Langkawi","Sungai Petani"],
    "Kelantan": ["Kota Bharu","Pasir Mas","Tanah Merah","Tumpat"],
    "Melaka": ["Alor Gajah","Jasin","Melaka Tengah"],
    "Negeri Sembilan": ["Jempol","Port Dickson","Seremban"],
    "Pahang": ["Bentong","Kuantan","Pekan","Raub","Temerloh"],
    "Perak": ["Ipoh","Kampar","Kuala Kangsar","Manjung","Taiping"],
    "Perlis": ["Kangar"],
    "Penang": ["George Town","Seberang Perai"],
    "Sabah": ["Kota Kinabalu","Sandakan","Tawau"],
    "Sarawak": ["Kuching","Miri","Sibu"],
    "Selangor": ["Klang","Petaling Jaya","Shah Alam","Subang Jaya"],
    "Terengganu": ["Dungun","Kemaman","Kuala Terengganu"],
    "Kuala Lumpur": ["Kuala Lumpur"],
    "Putrajaya": ["Putrajaya"]
  },
  "Singapore": {
    "Central Region": ["Bishan","Bukit Merah","Bukit Timah","Geylang","Marina South","Novena","Queenstown","Toa Payoh"],
    "East Region": ["Bedok","Changi","Pasir Ris","Tampines"],
    "North Region": ["Sembawang","Woodlands","Yishun"],
    "North-East Region": ["Ang Mo Kio","Hougang","Punggol","Sengkang","Serangoon"],
    "West Region": ["Bukit Batok","Bukit Panjang","Choa Chu Kang","Clementi","Jurong East","Jurong West"]
  },
  "United Arab Emirates": {
    "Abu Dhabi": ["Abu Dhabi City","Al Ain","Madinat Zayed","Ruwais"],
    "Dubai": ["Dubai City","Jebel Ali","Hatta"],
    "Sharjah": ["Sharjah City","Kalba","Khor Fakkan"],
    "Ajman": ["Ajman City","Manama","Masfut"],
    "Umm Al Quwain": ["Umm Al Quwain City"],
    "Ras Al Khaimah": ["Ras Al Khaimah City","Al Jazirah Al Hamra"],
    "Fujairah": ["Fujairah City","Dibba Al-Fujairah"]
  },
  "Saudi Arabia": {
    "Riyadh": ["Riyadh","Al Kharj","Diriyah","Dawadmi"],
    "Makkah": ["Makkah","Jeddah","Taif","Rabigh"],
    "Madinah": ["Madinah","Yanbu","Badr","Al Ula"],
    "Eastern Province": ["Dammam","Dhahran","Al Khobar","Jubail","Qatif","Hofuf"],
    "Asir": ["Abha","Khamis Mushait","Bisha"],
    "Tabuk": ["Tabuk","Duba","Haql"],
    "Hail": ["Hail"],
    "Northern Borders": ["Arar","Rafha"],
    "Jazan": ["Jazan","Sabya","Abu Arish"],
    "Najran": ["Najran"],
    "Al Baha": ["Al Baha","Baljurashi"],
    "Al Jawf": ["Sakaka","Dumat Al Jandal"],
    "Qassim": ["Buraidah","Unaizah","Al Rass"]
  },
  "United Kingdom": {
    "England": ["Bath","Birmingham","Bristol","Cambridge","Canterbury","Chester","Coventry","Derby","Durham","Exeter","Gloucester","Leeds","Leicester","Liverpool","London","Manchester","Newcastle","Norwich","Nottingham","Oxford","Plymouth","Portsmouth","Sheffield","Southampton","Stoke-on-Trent","Sunderland","Wolverhampton","Worcester","York"],
    "Scotland": ["Aberdeen","Dundee","Edinburgh","Glasgow","Inverness","Perth","Stirling"],
    "Wales": ["Cardiff","Swansea","Newport","Bangor","St Davids","Wrexham"],
    "Northern Ireland": ["Belfast","Derry","Lisburn","Newry","Armagh"]
  },
  "United States": {
    "Alabama": ["Birmingham","Huntsville","Mobile","Montgomery","Tuscaloosa"],
    "Alaska": ["Anchorage","Fairbanks","Juneau"],
    "Arizona": ["Chandler","Gilbert","Glendale","Mesa","Phoenix","Scottsdale","Tempe","Tucson"],
    "Arkansas": ["Fayetteville","Fort Smith","Little Rock"],
    "California": ["Bakersfield","Fresno","Irvine","Long Beach","Los Angeles","Oakland","Sacramento","San Diego","San Francisco","San Jose","Santa Clara"],
    "Colorado": ["Aurora","Colorado Springs","Denver","Fort Collins","Lakewood"],
    "Connecticut": ["Bridgeport","Hartford","New Haven","Stamford"],
    "Delaware": ["Dover","Wilmington"],
    "Florida": ["Fort Lauderdale","Jacksonville","Miami","Orlando","St. Petersburg","Tampa"],
    "Georgia": ["Atlanta","Augusta","Columbus","Savannah"],
    "Hawaii": ["Hilo","Honolulu"],
    "Idaho": ["Boise","Idaho Falls","Nampa"],
    "Illinois": ["Aurora","Chicago","Naperville","Peoria","Rockford","Springfield"],
    "Indiana": ["Evansville","Fort Wayne","Indianapolis","South Bend"],
    "Iowa": ["Cedar Rapids","Davenport","Des Moines"],
    "Kansas": ["Kansas City","Overland Park","Topeka","Wichita"],
    "Kentucky": ["Lexington","Louisville"],
    "Louisiana": ["Baton Rouge","Lafayette","New Orleans","Shreveport"],
    "Maine": ["Augusta","Bangor","Portland"],
    "Maryland": ["Annapolis","Baltimore","Frederick","Rockville"],
    "Massachusetts": ["Boston","Cambridge","Springfield","Worcester"],
    "Michigan": ["Ann Arbor","Detroit","Grand Rapids","Lansing"],
    "Minnesota": ["Duluth","Minneapolis","Rochester","Saint Paul"],
    "Mississippi": ["Biloxi","Gulfport","Jackson"],
    "Missouri": ["Columbia","Jefferson City","Kansas City","Springfield","St. Louis"],
    "Montana": ["Billings","Great Falls","Helena","Missoula"],
    "Nebraska": ["Lincoln","Omaha"],
    "Nevada": ["Henderson","Las Vegas","Reno"],
    "New Hampshire": ["Concord","Manchester","Nashua"],
    "New Jersey": ["Edison","Jersey City","Newark","Paterson","Trenton"],
    "New Mexico": ["Albuquerque","Las Cruces","Santa Fe"],
    "New York": ["Albany","Buffalo","New York City","Rochester","Syracuse","Yonkers"],
    "North Carolina": ["Charlotte","Durham","Greensboro","Raleigh","Winston-Salem"],
    "North Dakota": ["Bismarck","Fargo","Grand Forks"],
    "Ohio": ["Akron","Cincinnati","Cleveland","Columbus","Dayton","Toledo"],
    "Oklahoma": ["Norman","Oklahoma City","Tulsa"],
    "Oregon": ["Eugene","Portland","Salem"],
    "Pennsylvania": ["Allentown","Harrisburg","Philadelphia","Pittsburgh","Reading"],
    "Rhode Island": ["Cranston","Providence","Warwick"],
    "South Carolina": ["Charleston","Columbia","Greenville","North Charleston"],
    "South Dakota": ["Rapid City","Sioux Falls"],
    "Tennessee": ["Chattanooga","Knoxville","Memphis","Nashville"],
    "Texas": ["Arlington","Austin","Corpus Christi","Dallas","El Paso","Fort Worth","Houston","Laredo","San Antonio"],
    "Utah": ["Ogden","Provo","Salt Lake City","West Valley City"],
    "Vermont": ["Burlington","Montpelier"],
    "Virginia": ["Alexandria","Arlington","Chesapeake","Norfolk","Richmond","Virginia Beach"],
    "Washington": ["Bellevue","Seattle","Spokane","Tacoma","Vancouver"],
    "West Virginia": ["Charleston","Huntington","Morgantown"],
    "Wisconsin": ["Green Bay","Kenosha","Madison","Milwaukee"],
    "Wyoming": ["Casper","Cheyenne","Laramie"],
    "Washington D.C.": ["Washington D.C."]
  },
  "Canada": {
    "Alberta": ["Calgary","Edmonton","Lethbridge","Red Deer"],
    "British Columbia": ["Burnaby","Kelowna","Surrey","Vancouver","Victoria"],
    "Manitoba": ["Brandon","Winnipeg"],
    "New Brunswick": ["Fredericton","Moncton","Saint John"],
    "Newfoundland and Labrador": ["Corner Brook","St. John's"],
    "Nova Scotia": ["Dartmouth","Halifax","Sydney"],
    "Ontario": ["Brampton","Hamilton","London","Mississauga","Ottawa","Toronto","Windsor"],
    "Prince Edward Island": ["Charlottetown"],
    "Quebec": ["Gatineau","Laval","Montreal","Quebec City","Sherbrooke"],
    "Saskatchewan": ["Regina","Saskatoon"]
  },
  "Australia": {
    "Australian Capital Territory": ["Canberra"],
    "New South Wales": ["Newcastle","Sydney","Wollongong"],
    "Northern Territory": ["Alice Springs","Darwin"],
    "Queensland": ["Brisbane","Cairns","Gold Coast","Sunshine Coast","Townsville"],
    "South Australia": ["Adelaide","Mount Gambier"],
    "Tasmania": ["Hobart","Launceston"],
    "Victoria": ["Geelong","Melbourne"],
    "Western Australia": ["Bunbury","Mandurah","Perth"]
  },
  "China": {
    "Anhui": ["Hefei","Wuhu"],
    "Beijing": ["Beijing"],
    "Chongqing": ["Chongqing"],
    "Fujian": ["Fuzhou","Xiamen"],
    "Guangdong": ["Dongguan","Foshan","Guangzhou","Shenzhen","Zhuhai"],
    "Guangxi": ["Guilin","Nanning"],
    "Guizhou": ["Guiyang"],
    "Hainan": ["Haikou","Sanya"],
    "Hebei": ["Shijiazhuang","Tangshan"],
    "Heilongjiang": ["Harbin"],
    "Henan": ["Zhengzhou","Luoyang"],
    "Hubei": ["Wuhan"],
    "Hunan": ["Changsha"],
    "Jiangsu": ["Nanjing","Suzhou","Wuxi"],
    "Jiangxi": ["Nanchang"],
    "Jilin": ["Changchun"],
    "Liaoning": ["Dalian","Shenyang"],
    "Inner Mongolia": ["Hohhot"],
    "Ningxia": ["Yinchuan"],
    "Qinghai": ["Xining"],
    "Shaanxi": ["Xi'an"],
    "Shandong": ["Jinan","Qingdao"],
    "Shanghai": ["Shanghai"],
    "Shanxi": ["Taiyuan"],
    "Sichuan": ["Chengdu"],
    "Tianjin": ["Tianjin"],
    "Tibet": ["Lhasa"],
    "Xinjiang": ["Urumqi"],
    "Yunnan": ["Kunming"],
    "Zhejiang": ["Hangzhou","Ningbo","Wenzhou"]
  },
  "Japan": {
    "Hokkaido": ["Sapporo","Asahikawa","Hakodate"],
    "Tohoku": ["Sendai","Akita","Aomori","Fukushima","Morioka","Yamagata"],
    "Kanto": ["Chiba","Kawasaki","Saitama","Tokyo","Yokohama"],
    "Chubu": ["Nagoya","Hamamatsu","Niigata","Shizuoka","Kanazawa"],
    "Kansai": ["Kobe","Kyoto","Osaka","Nara"],
    "Chugoku": ["Hiroshima","Okayama"],
    "Shikoku": ["Matsuyama","Takamatsu"],
    "Kyushu": ["Fukuoka","Kagoshima","Kumamoto","Nagasaki","Oita"]
  },
  "South Korea": {
    "Seoul": ["Seoul"],
    "Busan": ["Busan"],
    "Daegu": ["Daegu"],
    "Incheon": ["Incheon"],
    "Gwangju": ["Gwangju"],
    "Daejeon": ["Daejeon"],
    "Ulsan": ["Ulsan"],
    "Gyeonggi": ["Suwon","Seongnam","Goyang","Yongin","Bucheon","Ansan","Anyang"],
    "Gangwon": ["Chuncheon","Wonju","Gangneung"],
    "Chungcheong": ["Cheongju","Cheonan","Asan"],
    "Jeolla": ["Jeonju","Mokpo","Yeosu","Suncheon"],
    "Gyeongsang": ["Changwon","Gimhae","Pohang","Gumi","Gyeongju"],
    "Jeju": ["Jeju City","Seogwipo"]
  },
  "Philippines": {
    "NCR": ["Caloocan","Las Piñas","Makati","Manila","Pasay","Pasig","Quezon City","Taguig"],
    "CAR": ["Baguio","Tabuk"],
    "Ilocos Region": ["Dagupan","Laoag","San Fernando","Vigan"],
    "Cagayan Valley": ["Cauayan","Santiago","Tuguegarao"],
    "Central Luzon": ["Angeles","Balanga","Cabanatuan","Malolos","Olongapo","San Fernando","Tarlac"],
    "CALABARZON": ["Antipolo","Batangas","Calamba","Dasmariñas","Lipa","Lucena","San Pablo"],
    "MIMAROPA": ["Calapan","Puerto Princesa"],
    "Bicol Region": ["Legazpi","Naga","Sorsogon"],
    "Western Visayas": ["Bacolod","Iloilo City","Roxas"],
    "Central Visayas": ["Bogo","Cebu City","Lapu-Lapu","Mandaue","Tagbilaran","Talisay"],
    "Eastern Visayas": ["Ormoc","Tacloban"],
    "Zamboanga Peninsula": ["Dipolog","Pagadian","Zamboanga City"],
    "Northern Mindanao": ["Cagayan de Oro","Iligan","Malaybalay","Valencia"],
    "Davao Region": ["Davao City","Digos","Panabo","Tagum"],
    "SOCCSKSARGEN": ["General Santos","Kidapawan","Koronadal","Tacurong"],
    "Caraga": ["Bislig","Butuan","Surigao"],
    "BARMM": ["Cotabato City","Marawi"]
  },
  "Indonesia": {
    "Bali": ["Denpasar","Singaraja"],
    "Banten": ["Serang","South Tangerang","Tangerang"],
    "DKI Jakarta": ["Central Jakarta","East Jakarta","North Jakarta","South Jakarta","West Jakarta"],
    "West Java": ["Bandung","Bekasi","Bogor","Depok","Sukabumi"],
    "Central Java": ["Semarang","Solo","Magelang","Pekalongan"],
    "East Java": ["Malang","Surabaya","Kediri","Madiun"],
    "Yogyakarta": ["Yogyakarta"],
    "North Sumatra": ["Medan","Binjai","Pematang Siantar"],
    "South Sumatra": ["Palembang","Prabumulih"],
    "West Sumatra": ["Padang","Bukittinggi"],
    "Riau": ["Pekanbaru","Dumai"],
    "South Sulawesi": ["Makassar","Palopo","Parepare"],
    "East Kalimantan": ["Balikpapan","Samarinda"],
    "South Kalimantan": ["Banjarmasin"],
    "West Kalimantan": ["Pontianak"],
    "Papua": ["Jayapura"],
    "West Papua": ["Manokwari","Sorong"]
  },
  "Thailand": {
    "Bangkok": ["Bangkok"],
    "Central": ["Ayutthaya","Nakhon Pathom","Nonthaburi","Pathum Thani","Samut Prakan","Samut Sakhon"],
    "Eastern": ["Chachoengsao","Chanthaburi","Chon Buri","Pattaya","Rayong","Trat"],
    "Northern": ["Chiang Mai","Chiang Rai","Lampang","Lamphun","Mae Hong Son","Nan","Phayao","Phrae"],
    "Northeastern": ["Khon Kaen","Khorat","Nakhon Ratchasima","Ubon Ratchathani","Udon Thani"],
    "Southern": ["Hat Yai","Krabi","Nakhon Si Thammarat","Phuket","Songkhla","Surat Thani","Trang"],
    "Western": ["Kanchanaburi","Hua Hin","Prachuap Khiri Khan","Ratchaburi"]
  },
  "Vietnam": {
    "Northern": ["Hai Phong","Ha Long","Hanoi","Lao Cai","Nam Dinh","Ninh Binh","Thai Nguyen","Viet Tri"],
    "Central": ["Da Nang","Hue","Nha Trang","Quy Nhon","Vinh"],
    "Southern": ["Bien Hoa","Can Tho","Da Lat","Ho Chi Minh City","My Tho","Vung Tau"]
  },
  "Myanmar": {
    "Ayeyarwady Region": ["Pathein","Hinthada"],
    "Bago Region": ["Bago","Pyay"],
    "Kachin State": ["Myitkyina"],
    "Kayah State": ["Loikaw"],
    "Kayin State": ["Hpa-An"],
    "Magway Region": ["Magway","Pakokku"],
    "Mandalay Region": ["Mandalay","Meiktila","Pyin Oo Lwin"],
    "Mon State": ["Mawlamyine"],
    "Rakhine State": ["Sittwe"],
    "Sagaing Region": ["Monywa","Sagaing"],
    "Shan State": ["Kengtung","Lashio","Taunggyi"],
    "Tanintharyi Region": ["Dawei","Myeik"],
    "Yangon Region": ["Yangon"]
  },
  "Turkey": {
    "Marmara": ["Bursa","Edirne","Istanbul","Kocaeli","Sakarya","Tekirdağ"],
    "Aegean": ["Afyon","Aydın","Denizli","İzmir","Kütahya","Manisa","Muğla","Uşak"],
    "Mediterranean": ["Adana","Antalya","Hatay","Mersin","Osmaniye"],
    "Central Anatolia": ["Aksaray","Ankara","Eskişehir","Kayseri","Konya","Sivas"],
    "Black Sea": ["Amasya","Ordu","Samsun","Trabzon","Zonguldak"],
    "Eastern Anatolia": ["Elazığ","Erzurum","Malatya","Van"],
    "Southeastern Anatolia": ["Diyarbakır","Gaziantep","Mardin","Şanlıurfa"]
  },
  "Egypt": {
    "Lower Egypt": ["Alexandria","Damietta","Kafr El Sheikh","Mansoura","Port Said","Tanta"],
    "Upper Egypt": ["Aswan","Asyut","Luxor","Minya","Qena","Sohag"],
    "Cairo Region": ["Cairo","Giza","Helwan","6th of October"],
    "Canal Zone": ["Ismailia","Port Said","Suez"],
    "Sinai": ["Arish","Sharm El Sheikh"],
    "Western Desert": ["Siwa"]
  },
  "Nigeria": {
    "South West": ["Abeokuta","Ibadan","Ikeja","Lagos","Oshogbo"],
    "South East": ["Aba","Awka","Enugu","Owerri","Umuahia"],
    "South South": ["Asaba","Benin City","Calabar","Port Harcourt","Uyo","Warri"],
    "North Central": ["Abuja","Ilorin","Jos","Lokoja","Makurdi","Minna"],
    "North East": ["Bauchi","Gombe","Maiduguri","Yola"],
    "North West": ["Kaduna","Kano","Katsina","Sokoto","Zaria"]
  },
  "Kenya": {
    "Central": ["Kiambu","Murang'a","Nyeri","Thika"],
    "Coast": ["Kilifi","Malindi","Mombasa"],
    "Eastern": ["Embu","Machakos","Meru"],
    "Nairobi": ["Nairobi"],
    "North Eastern": ["Garissa","Wajir"],
    "Nyanza": ["Kisii","Kisumu"],
    "Rift Valley": ["Eldoret","Nakuru","Naivasha"],
    "Western": ["Bungoma","Kakamega"]
  },
  "South Africa": {
    "Eastern Cape": ["East London","Mthatha","Port Elizabeth"],
    "Free State": ["Bloemfontein","Welkom"],
    "Gauteng": ["Johannesburg","Pretoria","Soweto"],
    "KwaZulu-Natal": ["Durban","Pietermaritzburg","Richards Bay"],
    "Limpopo": ["Polokwane","Thohoyandou"],
    "Mpumalanga": ["Mbombela","Witbank"],
    "North West": ["Mahikeng","Rustenburg"],
    "Northern Cape": ["Kimberley","Upington"],
    "Western Cape": ["Cape Town","George","Stellenbosch"]
  },
  "Germany": {
    "Baden-Württemberg": ["Freiburg","Heidelberg","Karlsruhe","Mannheim","Stuttgart","Ulm"],
    "Bavaria": ["Augsburg","Munich","Nuremberg","Regensburg","Würzburg"],
    "Berlin": ["Berlin"],
    "Brandenburg": ["Cottbus","Potsdam"],
    "Bremen": ["Bremen","Bremerhaven"],
    "Hamburg": ["Hamburg"],
    "Hesse": ["Darmstadt","Frankfurt","Kassel","Wiesbaden"],
    "Lower Saxony": ["Braunschweig","Göttingen","Hannover","Oldenburg","Osnabrück"],
    "Mecklenburg-Vorpommern": ["Rostock","Schwerin"],
    "North Rhine-Westphalia": ["Bonn","Cologne","Dortmund","Düsseldorf","Essen","Münster"],
    "Rhineland-Palatinate": ["Koblenz","Mainz","Trier"],
    "Saarland": ["Saarbrücken"],
    "Saxony": ["Chemnitz","Dresden","Leipzig"],
    "Saxony-Anhalt": ["Halle","Magdeburg"],
    "Schleswig-Holstein": ["Kiel","Lübeck"],
    "Thuringia": ["Erfurt","Jena","Weimar"]
  },
  "France": {
    "Île-de-France": ["Paris","Boulogne-Billancourt","Versailles"],
    "Provence-Alpes-Côte d'Azur": ["Marseille","Nice","Toulon","Aix-en-Provence"],
    "Auvergne-Rhône-Alpes": ["Lyon","Grenoble","Saint-Étienne","Clermont-Ferrand"],
    "Nouvelle-Aquitaine": ["Bordeaux","Limoges","Poitiers"],
    "Occitanie": ["Toulouse","Montpellier","Nîmes","Perpignan"],
    "Hauts-de-France": ["Lille","Amiens"],
    "Grand Est": ["Strasbourg","Reims","Metz","Nancy"],
    "Pays de la Loire": ["Nantes","Angers","Le Mans"],
    "Brittany": ["Rennes","Brest","Saint-Malo"],
    "Normandy": ["Caen","Rouen","Le Havre"],
    "Centre-Val de Loire": ["Orléans","Tours"],
    "Bourgogne-Franche-Comté": ["Dijon","Besançon"],
    "Corsica": ["Ajaccio","Bastia"]
  },
  "Brazil": {
    "São Paulo": ["Campinas","Guarulhos","Santos","São Paulo"],
    "Rio de Janeiro": ["Niterói","Rio de Janeiro"],
    "Minas Gerais": ["Belo Horizonte","Uberlândia"],
    "Bahia": ["Salvador","Feira de Santana"],
    "Paraná": ["Curitiba","Londrina","Maringá"],
    "Rio Grande do Sul": ["Porto Alegre","Caxias do Sul"],
    "Pernambuco": ["Recife","Jaboatão dos Guararapes"],
    "Ceará": ["Fortaleza"],
    "Pará": ["Belém"],
    "Maranhão": ["São Luís"],
    "Santa Catarina": ["Florianópolis","Joinville"],
    "Goiás": ["Goiânia"],
    "Amazonas": ["Manaus"],
    "Distrito Federal": ["Brasília"]
  },
  "Mexico": {
    "Aguascalientes": ["Aguascalientes"],
    "Baja California": ["Ensenada","Mexicali","Tijuana"],
    "Chihuahua": ["Chihuahua","Ciudad Juárez"],
    "Coahuila": ["Saltillo","Torreón"],
    "Jalisco": ["Guadalajara","Puerto Vallarta","Zapopan"],
    "México": ["Ecatepec","Naucalpan","Toluca"],
    "Mexico City": ["Mexico City"],
    "Nuevo León": ["Monterrey","San Nicolás","San Pedro Garza García"],
    "Puebla": ["Puebla"],
    "Querétaro": ["Querétaro"],
    "Quintana Roo": ["Cancún","Playa del Carmen"],
    "Yucatán": ["Mérida"],
    "Veracruz": ["Veracruz","Xalapa"],
    "Guanajuato": ["Guanajuato","León"]
  }
};

/* ── Currency map (keyed by country name → ISO currency code) ── */
const COUNTRY_CURRENCY = {
  "Bangladesh":"BDT","India":"INR","Pakistan":"PKR","Nepal":"NPR","Sri Lanka":"LKR",
  "Malaysia":"MYR","Singapore":"SGD","United Arab Emirates":"AED","Saudi Arabia":"SAR",
  "United Kingdom":"GBP","United States":"USD","Canada":"CAD","Australia":"AUD",
  "China":"CNY","Japan":"JPY","South Korea":"KRW","Philippines":"PHP",
  "Indonesia":"IDR","Thailand":"THB","Vietnam":"VND","Myanmar":"MMK",
  "Turkey":"TRY","Egypt":"EGP","Nigeria":"NGN","Kenya":"KES","South Africa":"ZAR",
  "Germany":"EUR","France":"EUR","Brazil":"BRL","Mexico":"MXN"
};

/**
 * Wire up cascading dropdowns.
 * Call once on DOMContentLoaded:
 *   initLocationDropdowns('countryField', 'districtState', 'cityUpazila');
 *
 * @param {string} countryId   – <select> id for country
 * @param {string} stateId     – <select> id for state / division
 * @param {string} cityId      – <select> id for city / district
 * @param {string} [currencyId] – optional <select> id to auto-set currency
 */
function initLocationDropdowns(countryId, stateId, cityId, currencyId) {
  const countryEl = document.getElementById(countryId);
  const stateEl   = document.getElementById(stateId);
  const cityEl    = document.getElementById(cityId);

  // Populate country list
  countryEl.innerHTML = '<option value="">Select Country</option>';
  Object.keys(LOCATION_DATA).sort().forEach(c => {
    const opt = document.createElement('option');
    opt.value = c; opt.textContent = c;
    countryEl.appendChild(opt);
  });

  function populateStates() {
    const country = countryEl.value;
    stateEl.innerHTML = '<option value="">Select State / Division</option>';
    cityEl.innerHTML  = '<option value="">Select City / District</option>';
    if (country && LOCATION_DATA[country]) {
      Object.keys(LOCATION_DATA[country]).sort().forEach(s => {
        const opt = document.createElement('option');
        opt.value = s; opt.textContent = s;
        stateEl.appendChild(opt);
      });
    }
    // Auto-set currency
    if (currencyId && COUNTRY_CURRENCY[country]) {
      const cEl = document.getElementById(currencyId);
      if (cEl) cEl.value = COUNTRY_CURRENCY[country];
    }
  }

  function populateCities() {
    const country = countryEl.value;
    const state   = stateEl.value;
    cityEl.innerHTML = '<option value="">Select City / District</option>';
    if (country && state && LOCATION_DATA[country] && LOCATION_DATA[country][state]) {
      LOCATION_DATA[country][state].forEach(d => {
        const opt = document.createElement('option');
        opt.value = d; opt.textContent = d;
        cityEl.appendChild(opt);
      });
    }
  }

  countryEl.addEventListener('change', populateStates);
  stateEl.addEventListener('change', populateCities);

  // Set default if Bangladesh
  countryEl.value = 'Bangladesh';
  populateStates();
}
