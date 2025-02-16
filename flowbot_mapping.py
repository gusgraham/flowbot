from typing import List, Optional
import re
import folium
from folium.plugins import MarkerCluster, MiniMap
from folium.map import Marker
from jinja2 import Template
import tempfile
from flowbot_monitors import mappedFlowMonitors


class flowbotWebMap():

    mapHTMLFile: str
    Location01 = [57.8215748, -4.4383279]
    fmZoomLevel = 15
    # Location02 = [52.898668, -3.5078534]
    initialZoom = 6
    currentLocation: List
    currentZoom = 0
    mappedFMs: Optional[mappedFlowMonitors]

    def __init__(self):
        super().__init__()

        self.mapHTMLFile = ''
        self.currentLocation = self.Location01
        self.currentZoom = self.initialZoom
        self.mappedFMs = None

        self.initializeFolium()

    def initializeFolium(self):
        self.updateMap()

    def zoomTo(self, coords: Optional[List[float]], zoom_level: int):

        if coords is not None:
            self.currentLocation = coords
        self.currentZoom = zoom_level
        self.updateMapView()

    def updateMapView(self):

        if self.mapHTMLFile:
            with open(self.mapHTMLFile, 'r', encoding='utf-8') as file:
                map_html = file.read()

            # Use regular expressions to find and replace the center and zoom values
            map_html = re.sub(r'center: \[.*?\]', f'center: [{self.currentLocation[0]}, {self.currentLocation[1]}]', map_html)
            map_html = re.sub(r'zoom: \d+', f'zoom: {self.currentZoom}', map_html)

            # Write the modified HTML content back to the file
            with open(self.mapHTMLFile, 'w', encoding='utf-8') as file:
                file.write(map_html)

    def updateMap(self):

        m = None
        marker_cluster = None

        # Create a Folium map
        m = folium.Map(location=self.currentLocation, zoom_start=self.currentZoom)

        MiniMap(toggle_display=True, minimized=False, zoom_level_fixed=4).add_to(m)
        marker_cluster = MarkerCluster().add_to(m)

        click_template = """{% macro script(this, kwargs) %}
            var {{ this.get_name() }} = L.marker(
                {{ this.location|tojson }},
                {{ this.options|tojson }}
            ).addTo({{ this._parent.get_name() }}).on('click', onClick);
        {% endmacro %}"""

        # Change template to custom template
        Marker._template = Template(click_template)

        if self.mappedFMs is not None:
            for monitor_name, monitor in self.mappedFMs.dictMappedFlowMonitors.items():
                latitude = monitor.latitude
                longitude = monitor.longitude
                fm_name = monitor.monitorName
                fm_status = 'Installed'  # You can set the status accordingly

                try:
                    if latitude is not None and longitude is not None:
                        folium.Marker([latitude, longitude], popup=f"{fm_name} ({fm_status})").add_to(marker_cluster)
                except Exception as e:
                    print(f"An unexpected error occurred for monitor {monitor_name}. Error message: {str(e)}")

        click_js = """function onClick(e) {
                        var popupHtml = e.target.getPopup().getContent();
                        var tempElement = $(popupHtml);
                        var popupText = tempElement.text();
                        new QWebChannel(qt.webChannelTransport, function (channel) {
                            var handler = channel.objects.handler;
                            handler.popupClicked(popupText);
                        });
                    }"""

        e = folium.Element(click_js)
        html = m.get_root()
        html.script.get_root().render()
        html.script._children[e.get_name()] = e

        map_html = m.get_root().render()

        # Find the last occurrence of </head> and insert the script before it
        map_html = re.sub(
            r'</head>', '    <script src="qrc:///qtwebchannel/qwebchannel.js"></script>\n</head>', map_html)

        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as temp_file:
            temp_file.write(map_html.encode('utf-8'))
            temp_file.flush()
            self.mapHTMLFile = temp_file.name

        # # return QUrl.fromLocalFile(self.temp_file_path)
        # self.mapHTMLFile = QUrl.fromLocalFile(temp_file_path)

    # def update(self):

    #     if self.temp_file_path:
    #         with open(self.temp_file_path, 'r', encoding='utf-8') as file:
    #             map_html = file.read()

    #         # Use regular expressions to find and replace the center and zoom values
    #         map_html = re.sub(
    #             r'center: \[.*?\]', f'center: [{self.currentLocation[0]}, {self.currentLocation[1]}]', map_html)
    #         map_html = re.sub(
    #             r'zoom: \d+', f'zoom: {self.currentZoom}', map_html)

    #         # Write the modified HTML content back to the file
    #         with open(self.temp_file_path, 'w', encoding='utf-8') as file:
    #             file.write(map_html)

    #         self.webEngineView.load(QUrl.fromLocalFile(self.temp_file_path))
