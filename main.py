import os
from qgis.PyQt.QtGui import QIcon
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QScrollArea, QWidget, QLineEdit, QAction
from qgis.core import QgsProject, QgsVectorLayer,QgsExpression, QgsFeatureRequest
from qgis.utils import iface

class Zooming:
    def __init__(self, iface):
        self.iface = iface
        self.action = None

    def initGui(self):
        icon_path = os.path.join(os.path.dirname(__file__), "icon.png")
        icon = QIcon(icon_path)
        
        self.action = QAction(icon, "Zooming", self.iface.mainWindow())
        self.action.setToolTip("Zoom to feature")
        self.action.triggered.connect(self.run_script)
        
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("&Zooming", self.action)
        
    def run_script(self):
        class Main(QDialog):
            def __init__(self):
                super().__init__()
                self.setWindowTitle("Choose a layer")
                self.setMinimumWidth(300)
                
                self.layout = QVBoxLayout()
                self.layout.addWidget(QLabel("Click a layer XD:"))
                
                scroll_area = QScrollArea()
                scroll_widget = QWidget()
                scroll_layout = QVBoxLayout()
                
                self.layers_dict = {}
                for layer in QgsProject.instance().mapLayers().values():
                    layer_name = None
                    if isinstance(layer, QgsVectorLayer):
                        layer_name = layer.name()
                    if layer_name not in self.layers_dict:
                        self.layers_dict[layer_name] = []
                    self.layers_dict[layer_name].append(layer)
                    
                for layer_name in self.layers_dict.keys():
                    btn = QPushButton(layer_name)
                    btn.clicked.connect(lambda checked, name = layer_name: self.select_layer(name))
                    scroll_layout.addWidget(btn)
                
                scroll_widget.setLayout(scroll_layout)
                scroll_area.setWidget(scroll_widget)
                scroll_area.setWidgetResizable(True)
                self.layout.addWidget(scroll_area)
                
                self.setLayout(self.layout)
                
                self.selected_field_name = None
            
            def select_layer(self, layer_name):
                self.selected_layer_name = layer_name
                self.selected_layers = self.layers_dict[layer_name]
                self.open_field_selection()
                self.accept()
                
            def open_field_selection(self):
                field_dialog = FieldSelector(self.selected_layers)
                if field_dialog.exec_():
                    self.selected_field_name = field_dialog.selected_field_name
                    value_dialog = Value(self.selected_layers, self.selected_field_name)
                    value_dialog.exec_()
            
        class FieldSelector(QDialog):
            def __init__(self, selected_layers):
                super().__init__()
                self.setWindowTitle("Choose a field")
                self.setMinimumWidth(300)
                
                self.layout = QVBoxLayout()
                self.layout.addWidget(QLabel("Click a field XD:"))
                
                scroll_area = QScrollArea()
                scroll_widget = QWidget()
                scroll_layout = QVBoxLayout()
                
                self.selected_layers = selected_layers
                self.fields_set = set()
                for layer in selected_layers:
                    self.fields_set.update([field.name() for field in layer.fields()])
                for field_name in sorted(self.fields_set):
                    btn = QPushButton(field_name)
                    btn.clicked.connect(lambda checked, name = field_name: self.select_field(name))
                    scroll_layout.addWidget(btn)
                
                scroll_widget.setLayout(scroll_layout)
                scroll_area.setWidget(scroll_widget)
                scroll_area.setWidgetResizable(True)
                self.layout.addWidget(scroll_area)
                
                self.setLayout(self.layout)
                
            def select_field(self, field_name):
                self.selected_field_name = field_name
                value_dialog = Value(self.selected_layers, self.selected_field_name)
                self.accept()
            
        class Value(QDialog):
            def __init__(self, selected_layers, selected_field_name):
                super().__init__()
                self.setWindowTitle("Enter Value")
                self.setMinimumWidth(300)

                self.selected_layers = selected_layers
                self.selected_field_name = selected_field_name

                self.layout = QVBoxLayout()
                self.layout.addWidget(QLabel(f"Enter value for field: {self.selected_field_name}"))

                self.value_input = QLineEdit()
                self.layout.addWidget(self.value_input)

                self.search_button = QPushButton("Search & Zoom")
                self.search_button.clicked.connect(self.find_and_zoom_to_feature)
                self.layout.addWidget(self.search_button)

                self.setLayout(self.layout)
                
                self.setMinimumWidth(300)
                
            def find_and_zoom_to_feature(self):
                
                field_name = self.selected_field_name
                field_value = self.value_input.text()
                
                if not field_name or not field_value:
                    iface.messageBar().pushMessage("Error", "Please enter a field value!", level = 3)
                    return
                
                found_features = []
                
                for layer in self.selected_layers:
                    if not layer:
                        continue
                        
                    if field_name not in [f.name() for f in layer.fields()]:
                        continue
                    
                    field_type = layer.fields().field(layer.fields().indexFromName(field_name)).typeName()
                    if field_type in ['Integer', 'Double']:
                        expression = f'"{field_name}" = {field_value}'
                    else:
                        expression = f'"{field_name}" = \'{field_value}\''
                    
                    request = QgsFeatureRequest().setFilterExpression(expression)
                
                    for feature in layer.getFeatures(request):
                        found_features.append(feature)
            
                if found_features:
                    for layer in self.selected_layers:
                        layer.removeSelection()
                        for feature in found_features:
                            layer.select(feature.id())
                    iface.mapCanvas().zoomToSelected(self.selected_layers[0])
                    iface.messageBar().pushMessage("Success", "Feature found and zoomed!", level=0)
                    self.accept()
            
                else:
                    iface.messageBar().pushMessage("Info", "No matching feature found.", level=1)
                    self.accept()
                
        dialog = Main()
        if dialog.exec_():
            selected_layer_name = dialog.selected_layer_name
            selected_field_name = dialog.selected_field_name
            print (f"Selected layer: {selected_layer_name}")
            print (f"Selected field: {selected_field_name}")

            def unload(self):
                if self.action:
                    self.iface.removeToolBarIcon(self.action)
