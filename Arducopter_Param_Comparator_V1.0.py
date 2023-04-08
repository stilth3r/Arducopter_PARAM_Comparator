import os
import csv
import sys
from typing import List
from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableView, QHeaderView, QPushButton, QFileDialog, QMessageBox, QAbstractItemView, QMenu, QAction, QVBoxLayout, QWidget, QSizePolicy, QMenuBar,  QLineEdit
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QColor
import qdarktheme

class ArdupilotParameterComparison(QMainWindow):
    def __init__(self):
        super().__init__()

        # autorise le drop de fichier dans la fenetre
        self.setAcceptDrops(True)

        # Initialisation de la fenêtre principale
        self.setWindowTitle("Comparaison de paramètres Ardupilot V1.01")
        self.setGeometry(100, 100, 800, 600)
        
              
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)

        file_menu = menubar.addMenu('Fichier')
        import_action = QAction('Importer', self)
        import_action.setShortcut('Ctrl+I')
        import_action.triggered.connect(self.import_file)
        file_menu.addAction(import_action)

        
        # Tableau des paramètres
        self.table_view = QTableView(self)
        self.table_view.setGeometry(10, 70, 780, 520)
        self.table_model = QStandardItemModel(self)
        self.table_view.setModel(self.table_model)
        self.table_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setCentralWidget(self.table_view)

        self.filter_edit = QLineEdit(self)
        self.filter_edit.setPlaceholderText("Filtrer...")
        self.filter_edit.textChanged.connect(self.filter_data)
        self.filter_edit.move(100, 1)
        self.filter_edit.resize(150, 24)

        self.file_names = []

        # Récupération de l'en-tête de la table view
        header = self.table_view.horizontalHeader()

        # Activation du mode de menu contextuel
        header.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        # Connexion du signal du menu contextuel à une méthode
        header.customContextMenuRequested.connect(self.show_column_menu)

    # Fonction d'importation de fichier
    def import_file(self, path):
        # Ouverture d'une boîte de dialogue pour la sélection d'un fichier
        if path == False : 
            file_name, _ = QFileDialog.getOpenFileName(self, 'Importer un fichier', '', 'Fichiers de paramètres (*.param)')
        else : 
            file_name = path

        # Vérification si un fichier a été sélectionné
        if file_name:
            # Vérification si le fichier a déjà été importé
            if file_name in self.file_names:
                QMessageBox.warning(self, 'Attention', 'Le fichier a déjà été importé.', QMessageBox.Ok)
                return

            self.file_names.append(file_name)
            file_basename = os.path.splitext(os.path.basename(file_name))[0]

            # Ouverture du fichier CSV
            with open(file_name, 'r') as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=',')
                param_dict = {}

                # Ajout des paramètres au dictionnaire
                for row in csv_reader:
                    if len(row) == 2:
                        param_dict[row[0]] = row[1]

                # Ajout des entêtes
                if len(self.file_names) == 1:
                    self.table_model.setHorizontalHeaderLabels(['Nom', file_basename])
                    for param_name, param_value in param_dict.items():
                        self.table_model.appendRow([QStandardItem(param_name), QStandardItem(param_value)])
                else:
                    # Ajout des valeurs de paramètres correspondantes
                    for i in range(self.table_model.rowCount()):
                        item = self.table_model.item(i, 0)
                        if item.text() in param_dict:
                            self.table_model.setItem(i, len(self.file_names), QStandardItem(param_dict[item.text()]))
                            del param_dict[item.text()]

                    # Ajout des nouveaux paramètres
                    for param_name, param_value in param_dict.items():
                        self.table_model.appendRow([QStandardItem(param_name), None])
                        self.table_model.setItem(self.table_model.rowCount()-1, len(self.file_names), QStandardItem(param_value))

                    # Tri des paramètres par ordre alphabétique
                    self.table_model.sort(0)

                    # Ajout de l'entête pour le nouveau fichier
                    self.table_model.setHorizontalHeaderItem(len(self.file_names), QStandardItem(file_basename))
                    if self.table_model.columnCount() > 2:
                        self.analyse()
    
    def analyse(self):
        num_columns = self.table_model.columnCount()

        for i in range(self.table_model.rowCount()):
            # Récupération du nom du paramètre de la première colonne
            param_name = self.table_model.index(i, 0).data()

            # Ignore les lignes où la première colonne est vide
            if not param_name:
                continue

            values = []

            # Récupération des valeurs de chaque colonne (en commençant par la deuxième)
            for j in range(1, num_columns):
                index = self.table_model.index(i, j)
                value = index.data()
                values.append(value)

            # Définition de la couleur de fond de la ligne en fonction des critères
            if all(v == values[0] for v in values[1:] if v is not None) and values[0] != "":
            #if all(v == values[0] for v in values if v and v.strip()):
                for j in range(num_columns):
                    item = self.table_model.item(i, j)
                    if item is not None:
                        item.setBackground(QColor('green'))
            elif len(set(values))-1 == num_columns - 2:
                for j in range(num_columns):
                    item = self.table_model.item(i, j)
                    if item is not None:
                        item.setBackground(QColor('red'))
            else:
                for j in range(num_columns):
                    item = self.table_model.item(i, j)
                    if item is not None:
                        item.setBackground(QColor('orange'))

    def show_column_menu(self, pos):
        # Récupération de la colonne sous le clic de souris
        index = self.table_view.horizontalHeader().logicalIndexAt(pos)
        
        # Création du menu contextuel
        menu = QMenu(self)
        if index > 0:
            delete_action = QAction("Supprimer la colonne", self)
            delete_action.triggered.connect(lambda: self.delete_column(index))
            menu.addAction(delete_action)

            # Affichage du menu contextuel
            menu.popup(self.table_view.horizontalHeader().viewport().mapToGlobal(pos))

    def delete_column(self, index):
        num_columns = self.table_model.columnCount()
        # Suppression de la colonne de la table model
        if num_columns > 2 : 
            self.table_model.removeColumn(index)
        else : 
            self.table_model.removeColumn(index)
            self.table_model.removeColumn(0)
        self.analyse()

    def dragEnterEvent(self, event):
        # autorise le drop uniquement si c'est un fichier .param
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().endswith('.param'):
                    event.accept()
                    return
        event.ignore()

    def dropEvent(self, event):
        # récupère le chemin absolu du premier fichier .param
        for url in event.mimeData().urls():
            path = str(url.toLocalFile())
            if path.endswith('.param'):
                # lance la procédure d'import avec le fichier déposé
                self.import_file(path)
                break

    def filter_data(self):
        # Récupération de la valeur du champ de texte
        filter_value = self.filter_edit.text().upper()

        # Si la valeur a au moins 3 caractères
        if len(filter_value) >= 3:
            # Filtrage des données du tableau
            for i in range(self.table_model.rowCount()):
                item = self.table_model.index(i, 0).data()
                if item is not None and filter_value in item:
                    self.table_view.setRowHidden(i, False)
                else:
                    self.table_view.setRowHidden(i, True)
        else:
            # Si la valeur a moins de 3 caractères, on affiche toutes les lignes
            for i in range(self.table_model.rowCount()):
                self.table_view.setRowHidden(i, False)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    qdarktheme.setup_theme()
    window = ArdupilotParameterComparison()
    window.show()
    sys.exit(app.exec_())

