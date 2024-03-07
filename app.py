# from flask import Flask, render_template, request, redirect, url_for
# from map_downloader import bounding_box, number_of_tiles, download_tiles
# from threading import Thread
# import time

# app = Flask(__name__)
# @app.route('/')
# def index():
#     flag = False
#     return render_template('map.html', flag=flag, points=[0,0,0,0], latitude=20.5937, longitude=78.9629, zoom_view=5)

# @app.route('/calculate_tiles', methods=['POST','GET'])
# def calculate_tiles():
#     global download_completed
#     download_completed = False
#     flag = True
#     latitude = request.form.get('latitude', type=float)
#     longitude = request.form.get('longitude', type=float)
#     distance_km_in = request.form.get('distance')
#     distance_km = float(distance_km_in )* 2
#     dir_name = request.form['directory']
#     max_zoom_level = request.form.get('zoom', type=int)
#     top, left, bottom, right = bounding_box(latitude, longitude, distance_km)
#     total_tiles = number_of_tiles(max_zoom_level, top, left, bottom, right)
    
#     if request.form['action'] == 'calculate':
#         expected_size = (total_tiles * 18)/(1024**2)
#         return render_template('map.html', total_tiles=total_tiles, expected_size=round(expected_size, 3),
#                                latitude=latitude, longitude=longitude, points=[top, left, bottom, right],
#                                flag=flag, zoom_view=10)
    
#     elif request.form['action'] == 'download':
#         download_thread = Thread(target=download_tiles, args=(max_zoom_level, dir_name, top, left, bottom, right))
#         download_thread.start()
#         download_thread.join() 
#         download_completed = True
#         return render_template('map.html', latitude=latitude, longitude=longitude,points=[top, left, bottom, right], flag=flag, zoom_view=8,download_completed=download_completed)
#     return "ERROR"


# if __name__ == '__main__':
#     #Jagrit Aggarwal
#     app.run(debug=True)



from flask import Flask, render_template, request, jsonify
from map_downloader import bounding_box, number_of_tiles, download_tiles
import concurrent.futures

app = Flask(__name__)

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
        expected_size = remaining_tiles * 18 / (1024 ** 2)
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

if __name__ == '__main__':
    app.run(debug=True)

