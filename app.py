from flask import Flask, render_template, request, jsonify, send_file
from map_downloader import bounding_box, number_of_tiles, download_tiles
import concurrent.futures
import os

app = Flask(__name__)
viewer_directory = ""

cwd = os.getcwd()
main = os.path.join(cwd,"map_tile")

@app.route('/')
def index():
    flag=False
    return render_template('map.html', flag=flag, points=[0,0,0,0], latitude=20.5937, longitude=78.9629, zoom_view=5,remaining_tiles = -1)

@app.route('/calculate_tiles', methods=['POST'])
def calculate_tiles():
    latitude = float(request.form['latitude'])
    longitude = float(request.form['longitude'])
    distance_km = float(request.form['distance']) * 2
    dir_name = request.form['directory']
    max_zoom_level = int(request.form['zoom'])

    top, left, bottom, right = bounding_box(latitude, longitude, distance_km)
    total_count,remaining_tiles,tiles_done = number_of_tiles(max_zoom_level, top, left, bottom, right,dir_name)

    if request.form['action'] == 'calculate':
        expected_size = remaining_tiles * 28 / (1024 ** 2)
        return render_template('map.html', remaining_tiles=remaining_tiles, expected_size=round(expected_size, 3),flag=True,points=[top, left, bottom, right],zoom_view=8,latitude=latitude,longitude=longitude)

    elif request.form['action'] == 'download':
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(download_tiles, max_zoom_level, dir_name, top, left, bottom, right)
            future.result()
        return render_template('map.html', download_completed=True,flag=True,points=[top, left, bottom, right],zoom_view=8,latitude=latitude,longitude=longitude)

    return "ERROR"

@app.route('/remaining_tiles', methods=['GET'])
def remaining_tiles():
    latitude = float(request.args.get('latitude'))
    longitude = float(request.args.get('longitude'))
    distance_km = float(request.args.get('distance')) * 2
    dir_name = request.args.get('directory')
    max_zoom_level = int(request.args.get('zoom'))
    top, left, bottom, right = bounding_box(latitude, longitude, distance_km)
    total_count,remaining_tiles,tiles_already_done = number_of_tiles(max_zoom_level, top, left, bottom, right, dir_name)
    return jsonify(total_count=total_count,tiles_done=tiles_already_done)


@app.route('/viewtiles', methods=['POST','GET'])
def view():
    folders = [folder for folder in os.listdir(main) if os.path.isdir(os.path.join(main, folder))]
    if request.method == 'POST':
        global viewer_directory
        viewer_directory = request.form['dir']
        return render_template('view.html',folders = folders,viewer_directory=viewer_directory)
    
    return render_template('view.html',folders = folders)




@app.route('/mytiles/<int:z>/<int:x>/<int:y>.jpeg')
def view_tiles(z, x, y):
    tile_path = f'map_tile/{viewer_directory}/{z}/{x}/{y}.jpeg'
    return send_file(tile_path)

if __name__ == '__main__':
    app.run(debug=True,port=5001)




if __name__ == '__main__':
    app.run(debug=True)

