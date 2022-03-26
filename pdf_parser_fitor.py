import fitz
import re

doc = fitz.open('H422 X-PRESS MULHACEN 21.3.2022.pdf')

"""values x0 and x1 in rectangle when rect(x0, y0, x1, y1)"""
shipper = (33, 140)
unit = (222, 290)
goods = (312, 445)
netw = (468, 502)
tare = (510, 547)
pod = (460, 500)
base_triangle = (33, 100, 547, 580)

total_starts = []   # lista över rektanglar för "Shipper :" på alla blad
total_stops = []    # lista över rektanglar för "Units :" på alla blad
total_height = 0.0  # loop över summan av höjderna på alla blad
total_words = []    # lista över alla dokumentets ord på alla blad
rect_pods = []     # lista över rektanglar för "Port of Discharge" på alla blad
words_in_rectangles = [] # lista för ord inom rektang*larna, utan "headers"
total_pods = [] # lista över rektanglar och namn för PODs
list_of_base_triangles = []
list_of_rectangles = []
list_of_tod_rectangles = []
final_tod_list = []

for page in doc:

    # starts
    starts = page.search_for("Shipper :")
    for rect in starts:
        total_starts.append(rect + (0, total_height, 0, total_height)) # lägger till på höjden för y0 och y1

    # stops
    stops = page.search_for("Units :")
    for rect in stops:
        total_stops.append(rect + (0, total_height, 0, total_height))

    # total_words
    words_in_page = page.get_text("words")
    for words in words_in_page:
        total_words.append([words[0], words[1] + total_height, words[2], words[3] + total_height, words[4]])

    # rect_pods
    pods = page.search_for('Port of discharge')
    for rect in pods:      
        rect_pods.append(rect + (0, total_height + 12.20998, 0, total_height + 16.08598)) # lägger till på y0 och y1 för att hitta POD
    
    # words_in_rectangles
    base_triangle = (33, 100 + total_height, 547, 580 + total_height) # Utgår från basrektangel (33, 100, 547, 580) och lägger på totalhöjden
    words_in_rectangles += [word for word in total_words if fitz.Rect(word[:4]).intersects(base_triangle)] # Tar fram alla ord inom rektangeln ovan
    list_of_base_triangles.append(base_triangle)
    
    total_height += page.rect.height # lägger till totalhöjden varje loop
       
pod_names = [' '.join([words[4] for words in total_words if fitz.Rect(words[:4]).intersects(pod)]) for pod in rect_pods] # Tar fram alla POD is en lista

rectangle = lambda x: fitz.Rect(33, total_starts[x][1], 580, total_stops[x][3])

for num, starts in enumerate(total_starts):
    list_of_rectangles.append(rectangle(num))

for triangles, tod in zip(list_of_base_triangles, pod_names):
    list_of_tod_rectangles.append([triangles[0], triangles[1], triangles[2], triangles[3], tod])

for rect in list_of_rectangles:
    counter = 0
    for tod in list_of_tod_rectangles:
        if tod[3] // rect[3] > 0 and counter == 0:
            final_tod_list.append(tod[4])
            counter == 1
            break

"""
FUNCTIONS BELOW
"""

def get_shipper(shipper, start, stop):

    rectangle = (shipper[0], start[1], shipper[1], stop[3])
    same_row = start[1]
    list_of_data = []
    str_of_words = ""
    counter = 0

    for word in words_in_rectangles:
        if fitz.Rect(word[:4]).intersects(rectangle):
            
            if same_row == word[1]:                                
                str_of_words += " " + word[4]

            elif same_row != word[1]:                             
                list_of_data.append(str_of_words.strip())
                str_of_words = word[4]

            same_row = word[1]

    for str in list_of_data:
        #matching SHIPPER
        shipper_match = re.search('Shipper :', str)

        if counter == 1:
            counter = 0
            return str

        elif shipper_match:
            counter = 1

def get_container_nos(unit, start, stop):

    rectangle = (unit[0], start[1], unit[1], stop[3])
    same_row = start[1]
    list_of_data = []
    list_of_cont = []
    str_of_words = ""

    for word in words_in_rectangles:
        if fitz.Rect(word[:4]).intersects(rectangle):
            if same_row == word[1]:
                str_of_words += " " + word[4]

            elif same_row != word[1]:
                list_of_data.append(str_of_words.strip())
                str_of_words = word[4]

            same_row = word[1]

    for str in list_of_data:
        #matching CONTAINER
        container_match = re.search(r'^\w{4}\s\d{6}\-\d', str)
        trim_cont = re.sub(r'[\s-]', '', str)

        if container_match:
            list_of_cont.append(trim_cont)

    return list_of_cont

def get_goods_info(goods, start, stop):

    rectangle = (goods[0], start[1], goods[1], stop[3])
    samma_rad = start
    lista_container_data = []
    lista_ord = ""

    for word in words_in_rectangles:

        if fitz.Rect(word[:4]).intersects(rectangle):

            if samma_rad == word[1]:                                # Om y-värdet på föregående rad i loop är samma som y-värdet för denna runda
                lista_ord += " " + word[4]

            elif samma_rad != word[1]:                              # Om y-värdet inte stämmer överens
                lista_container_data.append(lista_ord.strip())
                lista_ord = word[4]

            samma_rad = word[1]                                     # Sparar Y-värdet för raden för denna loop. Används i nästa runda

    lista_container_data.remove('')                                  # Tar bort första "" i listan
    
    customs_found = [id for id, value in enumerate(lista_container_data) if re.search(r'^Customs', value)]  # Söker efter "Customs" i lista_container_data och letar match
    
    lista_manifest_data = lista_container_data[customs_found[0]:]                                         # Ny lista som kopierar info från match med "Customs" och till slutet
    lista_container_data = lista_container_data[:customs_found[0]]                                            # Gör om lista och tar info fram till "Customs" match

    return lista_container_data, lista_manifest_data

def manifest_details(manifest_list):

    ocean_vessel_list = []
    final_pod_list = []
    counter_pod = 0
    counter_booking = 0

    for str in manifest_list:
        #matching CUSTOMS STATUS
        customs_match = re.search(r'(?<=Customs status \")\w', str)
        if customs_match:
            customs_status = customs_match.group()

        #matching OCEAN VESSEL
        transhipment_match = re.search(r'^Transhipment by', str)
        voy_match = re.search(r'^.+(?= Voy)', str)
        vessel_match = re.search(r'(?<=Transhipment by\s).+[^\s*Voy]', str)
        vessel_match_rest = re.search(r'^\w+[^ Voy]', str)

        if transhipment_match and vessel_match and voy_match:
            ocean_vessel_list.append(vessel_match.group())

        elif transhipment_match and not voy_match:
            ocean_vessel_list.append(vessel_match.group())

        elif voy_match and not transhipment_match:
            ocean_vessel_list.append(vessel_match_rest.group())

        ocean_vessel = ' '.join(ocean_vessel_list)

        #matching FINAL POD
        date_last_match = re.search(r'\d+\.+\d+\.+\d+$', str)
        etd_match = re.search(r'^ETD\s*\d+\.+\d+\.+\d+\s*\D+', str)
        only_etd_date = re.search(r'^(ETD\s*\d+\.+\d+\.+\d+)$', str)
        fpod_dual_dates = re.search(r'^(ETD\s*\d+\.+\d+\.+\d+\s*)(\D*)(\s+\d+\.+\d+\.+\d+)', str)
        fpod_single_date = re.search(r'^(ETD\s*\d+\.+\d+\.+\d+\s*)(\D*)', str)
        get_all_upper = re.search(r'^[\D]*', str)

        def del_fillers_pod(string):
            new_string = re.sub(r'\s*ETA\s*', '', string)
            new_string2 = re.sub(r',[^,]*', '', new_string)
            new_string3 = re.sub(r'\s$', '', new_string2)
            return new_string3

        if etd_match and date_last_match:
            final_pod_list.append(del_fillers_pod(fpod_dual_dates.group(2)))

        elif etd_match and not date_last_match:
            final_pod_list.append(del_fillers_pod(fpod_single_date.group(2)))

        elif counter_pod == 1:
            final_pod_list.append(del_fillers_pod(get_all_upper.group()))
            counter_pod = 0

        elif counter_pod == 2:
            final_pod_list.append(del_fillers_pod(get_all_upper.group()))
            counter_pod == 0

        elif only_etd_date:
            counter_pod = 1

        elif etd_match and not date_last_match:
            counter_pod = 2

        final_pod = ' '.join(final_pod_list)

        #matching BOOKING NUMBER
        ref_match = re.search(r'^ref', str, flags=re.IGNORECASE)

        def del_fillers_ref(string):
            new_string = re.sub(r'^[RrEeFf]{3}[:\.\s]*', '', string)
            new_string2 = re.sub(r'\s*OPS', '', new_string)
            return new_string2

        if ref_match and counter_booking != 1:
            booking_number = del_fillers_ref(str)

        elif counter_booking == 1:
            if transhipment_match:
                counter_booking = 0

            if not transhipment_match:
                booking_number = del_fillers_ref(str)
                counter_booking = 0

        elif customs_match:
            counter_booking = 1

    return_dict = {
        "BOOKING NUMBER": booking_number,
        "CUSTOMS STATUS": customs_status,
        "OCEAN VESSEL": ocean_vessel,
        "FINAL POD": final_pod
        }
    
    return return_dict

def goods_details(goods_list):
    list_of_unit_types = []
    list_of_goods = []

    for val in goods_list:

        match_unit_type = re.search(r"^\d{2}\'\D+", val)
        match_goods_info = re.search(r'^(\d+)\s+\w*\s+(\D+)', val)
        match_goods_info2 = re.search(r'^\D*$', val)

        if match_unit_type:
            list_of_unit_types.append(match_unit_type.group())

        if match_goods_info:
            list_of_goods.append(match_goods_info.group(1, 2))
        elif match_goods_info2:
            list_of_goods.append(match_goods_info2.group())

    return list_of_unit_types, list_of_goods

def get_netw(netw, start, stop):

    rectangle = (netw[0], start[1], netw[1], stop[3])
    list_of_data = []

    for word in words_in_rectangles:
        if fitz.Rect(word[:4]).intersects(rectangle):
            list_of_data.append(int(word[4]))

    if list_of_data:
        list_of_data.pop()

    return list_of_data

def get_tare(tare, start, stop):

    rectangle = (tare[0], start[1], tare[1], stop[3])
    list_of_data = []

    for word in words_in_rectangles:
        if fitz.Rect(word[:4]).intersects(rectangle):
            list_of_data.append(int(word[4]))

    if list_of_data:
        list_of_data.pop()

    return list_of_data

def run_it_all():
    bookings_count = len(total_starts)
    
    for booking_no in range(bookings_count):
        get_container_nos(unit, total_starts[booking_no], total_stops[booking_no])

print('hi')