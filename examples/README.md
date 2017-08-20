## istSOS-Data Analysis and statistical tool suite 

This section comprises of following parts:
* Installation Details
* OAT(Observation Analysis Tools) library
* Implemented OAT methods

Following implemented OAT methods in istSOS web-api:

### 1. Resample method 
The resample method calculates a new time-series with a given frequency by sampling values of a time-series with a different frequency.

It uses the following parameters:
* **Frequency**: An alphanumeric code specifying the desired frequency (A=year, M=month, W=week, D=day, H=hour, T=minute, S=second; e.g.: 1H10T) (string) 
* **Sampling method**: the sampling method (string)
* **FIll**: If not null it defines the method for filling no-data (string)
* **Limit**: if not null it defines the maximum numbers of allowed consecutive no-data valuas to be filled (integer)
* **How quality**: the sampling method for observation quality index (string)

![Resample method](images/resample1.png)
