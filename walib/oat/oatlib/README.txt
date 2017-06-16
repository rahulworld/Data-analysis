OAT (Observation Analysis Tool)
================================

Installation of the OAT extension pack to FREEWAT


1. copy the OAT folder under the FREEWAT plugin folder

2. Open the Freewat.py file in FREEWAT plugin folder and add the following line in the "initGUI" funtion (select appropriate location to set where the menu should be located):

    # Add oat to Main Menu
    from oat import oatInit
    oatInit.create_oat_menu(self)
    
3. Save and reload the plugin (or restart QGIS)

