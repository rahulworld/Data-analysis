## Examples of audio/video and SOS input support 

This section comprises of following parts:
* Setup tables in MapMint local instance 
* Importing data to the MapMint4ME from MapMint local instance
* Editing tables in the MapMint4ME for audio/video and SOS input data

### Setup tables in MapMint local instance

Before moving ahead, it would be necessary that **MapMint is installed properly** and you are able to access **Dashboard** module of MapMint web interface. Please visit **[Quick Check on installation](https://github.com/omshinde/MapMint4ME/tree/gsoc-2017-camera#quick-check-on-installation)** to confirm that you are able to access MapMint Dashboard. Once it is confirmed, you can proceed further with below-mentioned steps.

The next step requires to setup the **Tables** module of the MapMint web interface. Please refer to the following link which explains about setting up **Tables** module in MapMint. 
It explains in a step-by-step manner, the procedure to setup tables module.
[Successful publication of tables using Tables module in MapMint](https://github.com/mapmint/mapmint/issues/9)

Following the procedure mentioned in the above link for publishing tables using Tables module, I am creating following two tables for this example:

1. **test_table** by the title **Test_video**. The View name is Test Video View

![Test Video view](https://github.com/omshinde/MapMint4ME/blob/gsoc-2017-camera/examples/images/example_test_video.png)

It contains the following columns:
* Id  - integer 
* Name  - variable character(50)
* Description  -  text
* Upload  -  bytea (for binary files)
* Uid  -  integer

2. **sos_test_table** by the title **Test_SOS**. The View name is Test SOS View

![Test SOS view](https://github.com/omshinde/MapMint4ME/blob/gsoc-2017-camera/examples/images/example_test_sos.png)

It contains the following columns:
* Id  -  integer
* Name  -  variable character(50) 
* Description  -  text
* Sos  -  text
* Uid  -  integer

### Importing data to the MapMint4ME from the local instance

For this, please refer the following link explaining the process to import data from the local instance to the MapMint4ME.
[Using MapMint4ME for adding and editing tables](https://github.com/mapmint/mapmint/issues/10)

In the above link, I was using the emulator of [Android Studio](https://developer.android.com/studio/index.html). The Android Studio gives the advantage of directly importing the code from Version Control Systems such as Github, Mercurian *et cetera*. But, in this section, I will post images taken from testing with a real device.

After installing and running MapMint4ME, please click on **Import** icon. After clicking on the icon, you will see a screen like in the following image.

<p align="center">
<img src="https://github.com/omshinde/MapMint4ME/blob/gsoc-2017-camera/examples/images/add_server.png" width="280" height="400">
</p>

It is mentioning that there is no MapMint server registered yet. So Let's register it. Click on the icon for **Add a Server**, and you will see the following screen.

<p align="center">
<img src="https://github.com/omshinde/MapMint4ME/blob/gsoc-2017-camera/examples/images/server_details.png" width="280" height="400">
</p>

Click on the Add Server icon. Now, you will see a screen which is similar to the below image.

<p align="center">
<img src="https://github.com/omshinde/MapMint4ME/blob/gsoc-2017-camera/examples/images/server_added.png" width="280" height="400">
</p>

Now, click on the **import** icon at the side. the navigation bar will start moving till 100% and you will see a screen like the below image.

<p align="center">
<img src="https://github.com/omshinde/MapMint4ME/blob/gsoc-2017-camera/examples/images/import_done.png" width="280" height="400">
</p>

Now, from the **View** tab, you will see the tables imported from the MapMint.

<p align="center">
<img src="https://github.com/omshinde/MapMint4ME/blob/gsoc-2017-camera/examples/images/imported_tables.png" width="280" height="400">
</p>

Now, we can finally move towards seeing audio/video and SOS input data loaded into the tables.

### Audio/ Video recordings loading into the tables
In the **Edit** tab, you will be getting following four options:
* Select an existing photo
* Take a picture
* Select an existing video
* Record a video

It will be similar to the below image.

<p align="center">
<img src="https://github.com/omshinde/MapMint4ME/blob/gsoc-2017-camera/examples/images/options.png" width="280" height="400">
</p>

For video recording function, I can only choose **Test Video View** because as seen above in the table description, only this view contains a variable to store binary values.
Out of these options, **Selecting an existing video** and **Record a video**, options are added in GSoC 2017. On clicking on any of these options, you will be able to perform that corresponding function.
On clicking **ADD** icon, you will see that the value gets incremented in the **Test Video View**.

<p align="center">
<img src="https://github.com/omshinde/MapMint4ME/blob/gsoc-2017-camera/examples/images/video_in_table.png" width="280" height="400">
</p>

Also, by clicking on the **View** icon, and then on the **Test Video View**, you are able to see the captured video file in binary format with a proper timestamp. The following image shows the output:

<p align="center">
<img src="https://github.com/omshinde/MapMint4ME/blob/gsoc-2017-camera/examples/images/video_in_tables.png" width="280" height="400">
</p>

### SOS data loading into the table
#### NOTE: Before loading SOS data into the table, make sure that your SOS module is setup. Please refer [Setting up SOS module](https://github.com/omshinde/MapMint4ME/tree/gsoc-2017-camera/sos#setting-up-the-sensor-observation-service-sos) before moving forward.

Since the sensor readings will be obtained in string. It became important to have options to select among the SOS data input and the text input. Now, if the user wants to **import SOS reading directly**, then he can select **Import readings from SOS**. But, if the user wants to **enter text data** instead of SOS readings, then he can select **Enter text**.
The following options are present for the user and he has to select one amongst them.

* Import readings from SOS
* Enter text

#### First, we will see data imported from SOS

<p align="center">
<img src="https://github.com/omshinde/MapMint4ME/blob/gsoc-2017-camera/examples/images/options_SOS_new.png" width="280" height="400">
</p>

On clicking the option for **Import readings from SOS**
You will get to see the sensor readings displayed on the same screen. The readings displayed are in the following format **Humidity(%):Temperature(Deg Celsius):Smoke content(ppm)**

<p align="center">
<img src="https://github.com/omshinde/MapMint4ME/blob/gsoc-2017-camera/examples/images/select_sos_import.png" width="280" height="400">
</p>

The results after adding the files will be like in the following figure.

<p align="center">
<img src="https://github.com/omshinde/MapMint4ME/blob/gsoc-2017-camera/examples/images/add_sos.png" width="280" height="400">
</p>

As we can see, the readings obtained from the SOS module are stored in the Table.

#### Now, we will see data entered as text

<p align="center">
<img src="https://github.com/omshinde/MapMint4ME/blob/gsoc-2017-camera/examples/images/options_text.png" width="280" height="400">
</p>

On selecting the **Enter text** option, you will see a textarea merging on the same screen. Now, you can enter desired text data to be stored in the table.

<p align="center">
<img src="https://github.com/omshinde/MapMint4ME/blob/gsoc-2017-camera/examples/images/select_text_import.png" width="280" height="400">
</p>

After clicking on **Add**, the entered text will be stored in the table. Please consider the below image for reference.

<p align="center">
<img src="https://github.com/omshinde/MapMint4ME/blob/gsoc-2017-camera/examples/images/add_text.png" width="280" height="400">
</p>

The code can be seen at the [link](https://github.com/omshinde/MapMint4ME/tree/gsoc-2017-camera).