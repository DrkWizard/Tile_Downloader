from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
import os
import concurrent.futures
from map_downloader import number_of_tiles, download_tiles
import time,requests,re

app = Flask(__name__)

data = None
center = None
directory = None
zoom_lvl = None #ending zoom
zoom_start = None #starting zoom
northwest = None
northeast = None
southwest = None
southeast = None
center = None
total_count = 0
remaining_tiles = 0
tiles_done = 0

cwd = os.getcwd()
main = os.path.join(cwd, "map_tile")
if not os.path.exists(main):
    os.makedirs(main)

def modify(filepath, pattern, replacement):
    with open(filepath, "r+") as file:
        lines = file.readlines()
        modified_lines = [re.sub(pattern, replacement, line) for line in lines]
        file.seek(0)
        file.truncate()
        file.writelines(modified_lines)
        
def check_internet_connection():
    try:
        response = requests.get("http://www.google.com", timeout=4)
        if response.status_code == 200:
            return True 
        else:
            return False  
    except requests.ConnectionError:
        return False 

@app.route('/')
def index():
    internet = check_internet_connection()    
    return render_template('map.html',internet=internet)


@app.route('/calculate', methods=['POST'])
def calculate():
    global data, center, southeast, southwest, northeast, northwest, directory, zoom_lvl, remaining_tiles, total_count, tiles_done, zoom_start
    data = request.json
    center = data["value"][4]
    directory = data["value"][5]
    zoom_lvl = int(data["value"][6])
    zoom_start = int(data["value"][7])
    northwest = data["value"][0]
    northeast = data["value"][1]
    southwest = data["value"][2]
    southeast = data["value"][3]
    center = data["value"][8]
    total_count, remaining_tiles, tiles_done = number_of_tiles(zoom_start,zoom_lvl, northwest["lat"], northwest["lng"],southwest["lat"], southeast["lng"], directory)
    expected_size_kb = round(remaining_tiles * 28 , 3)
    expected_size_mb = round(expected_size_kb / 1024 , 3)
    expected_size_gb = round(expected_size_mb / 1024, 3)
    if expected_size_gb > 1:
        expected_size = f"{expected_size_gb} GB"
    elif expected_size_mb > 1:
        expected_size = f"{expected_size_mb} MB"
    else:
        expected_size = f"{expected_size_kb} KB"    
    return jsonify({'result': total_count, 'size': expected_size, 'remaining': remaining_tiles})


@app.route('/downloadstart')
def calculate_success():
    internet = check_internet_connection()    
    calculateSuccess = True
    return render_template("map.html",calculateSuccess=calculateSuccess,internet=internet)


@app.route('/downloadcont')
def continue_download():
    internet = check_internet_connection()    
    text_path = os.path.join(main, viewer_directory, "details.txt")
    with open(text_path, "r") as file:
        lines = file.readlines()
        top = lines[1].strip().split(sep=":")[1]
        left = lines[2].strip().split(sep=":")[1]
        bottom = lines[3].strip().split(sep=":")[1]
        right = lines[4].strip().split(sep=":")[1]
        zoom_s = lines[5].strip().split(sep=":")[1]
        zoom_e = lines[6].strip().split(sep=":")[1]
    points = [top,left,bottom,right]
    return render_template("continuemap.html", internet=internet,zoom_s=zoom_s,zoom_e=zoom_e,directory=viewer_directory,points = points)


@app.route('/download', methods=['POST'])
def download():
    try:
        d = request.json
        if d["value"] == 1:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(download_tiles,zoom_start, zoom_lvl, directory, northwest["lat"], northwest["lng"], southwest["lat"], southeast["lng"],center)
                result = future.result()
                print(result)
                if result:
                    return jsonify({'success': True})
                else:
                    raise Exception("Failed to download Tile")
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    
@app.route('/continue', methods=['POST'])
def continue_d():
    text_path = os.path.join(main, viewer_directory, "details.txt")
    with open(text_path, "r") as file:
        lines = file.readlines()
        top = lines[1].strip().split(sep=":")[1]
        left = lines[2].strip().split(sep=":")[1]
        bottom = lines[3].strip().split(sep=":")[1]
        right = lines[4].strip().split(sep=":")[1]
    try:
        d = request.json
        if d["value"] == 1:
            zoom_s = int(d["start"])
            zoom_e = int(d["end"])
            modify(text_path, r'^.*zoom start:.*$', f"zoom start: {zoom_s}")

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(download_tiles,int(zoom_s), int(zoom_e), viewer_directory, float(top), float(left), float(bottom), float(right),center)
                result = future.result()
                if result:
                    return jsonify({'success': True})
                else:
                    raise Exception("Failed to download Tile")
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

        
        
        
@app.route('/viewtiles', methods=['POST', 'GET'])
def view():
    folders = [folder for folder in os.listdir(main) if os.path.isdir(os.path.join(main, folder))]
    remaining_tiles = -1
    if request.method == 'POST':
        global viewer_directory
        viewer_directory = request.form['dir']
        try:
            details = True
            text_path = os.path.join(main, viewer_directory, "details.txt")
            
            with open(text_path, "r") as file:
                lines = file.readlines()
                top_h = lines[1].strip().split(sep=":")[1]
                left_h = lines[2].strip().split(sep=":")[1]
                bottom_h = lines[3].strip().split(sep=":")[1]
                right_h = lines[4].strip().split(sep=":")[1]
                zooms_h = lines[5].strip().split(sep=":")[1]
                zoom_h = lines[6].strip().split(sep=":")[1]
                marker_lat = lines[7].strip().split(sep=":")[1]
                marker_lng = lines[8].strip().split(sep=":")[1]
                
                total_count, remaining_tiles, tiles_done = number_of_tiles(int(zooms_h),int(zoom_h), float(top_h), float(left_h),float(bottom_h),float(right_h), viewer_directory)
            return render_template('view.html', folders=folders, viewer_directory=viewer_directory,details=details,remaining_tiles=remaining_tiles,marker_lat = marker_lat,marker_lng=marker_lng,date=lines[9], zooms = zooms_h,zoome=zoom_h )
        except:
            details = False
            marker_lat = 0
            marker_lng = 0
            lines = [0]*10
            print("All Folder therefore no text file read")
        return render_template('view.html', folders=folders, viewer_directory=viewer_directory,details=details,remaining_tiles=remaining_tiles )
    return render_template('view.html', folders=folders)


@app.route('/mytiles/<int:z>/<int:x>/<int:y>.jpeg')
def view_tiles(z, x, y):
    if viewer_directory != "all":
        tile_path = f'map_tile/{viewer_directory}/{z}/{x}/{y}.jpeg'
        if os.path.exists(tile_path):
                return send_from_directory(os.path.join(main, viewer_directory, str(z), str(x)), f'{y}.jpeg')
        return "done"
    else:
        folders = [folder for folder in os.listdir(main) if os.path.isdir(os.path.join(main, folder))]
        for folder in folders:
            tile_path = os.path.join(main, folder, str(z), str(x), f'{y}.jpeg')
            if os.path.exists(tile_path):
                return send_from_directory(os.path.join(main, folder, str(z), str(x)), f'{y}.jpeg')
    return "done"
        


@app.route('/remaining_tiles', methods=['GET'])
def remaining_tiles():
    total_count, remaining_tiles, tiles_done = number_of_tiles(zoom_start,zoom_lvl, northwest["lat"], northwest["lng"],southwest["lat"], southeast["lng"], directory)
    return jsonify(total_count=total_count, tiles_done=tiles_done)

@app.route('/remaining_tiles_cont', methods=['GET'])
def remaining_tiles_cont():
    text_path = os.path.join(main, viewer_directory, "details.txt")
    with open(text_path, "r") as file:
        lines = file.readlines()
        top = lines[1].strip().split(sep=":")[1]
        left = lines[2].strip().split(sep=":")[1]
        bottom = lines[3].strip().split(sep=":")[1]
        right = lines[4].strip().split(sep=":")[1]
        zoom_s = lines[5].strip().split(sep=":")[1]
        zoom_e = lines[6].strip().split(sep=":")[1]
    total_count, remaining_tiles, tiles_done = number_of_tiles(int(zoom_s),int(zoom_e), float(top), float(left),float(bottom),float(right), viewer_directory)
    return jsonify(total_count=total_count, tiles_done=tiles_done)





if __name__ == '__main__':
    app.run(debug=True, port=5000)
