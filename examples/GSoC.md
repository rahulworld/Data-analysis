# istSOS-Data Analysis and statistical tool suite 
> istsos2 provides easily manage your sensor network and distribute your data in a standard way.

>Mentors : [@massimiliano-cannata](https://github.com/massimiliano-cannata), [@mantonovic](https://github.com/mantonovic)


---
###istSOS

istSOS is an OGC SOS server implementation written in Python. istSOS allows for managing and dispatch observations from monitoring sensors according to the Sensor Observation Service standard.

The project provides also a Graphical user Interface that allows for easing the daily operations and a RESTful Web api for automatizing administration procedures.

![For installation and further information](http://istsos.org/)

[istSOS2 Github Repo.](https://github.com/istSOS/istsos2)

[Download istsos2 source code](https://sourceforge.net/projects/istsos/)

[Developers docs](http://istsos.org/en/latest/doc/#developers-docs)

---

###OAT(Observation Analysis Tool)

`OAT` is a Python package which is integrated in the istSOS through an interface exposing its features to modellers and non programmer users. OAT library Method class which is designated to represent a processing method. The library applies the behavioral visitor pattern which allows the separation of an algorithm from the object on which it operates.

From a dependency point of view, OAT takes advantage of the ![PANDAS](http://pandas.pydata.org/)(McKinney, 2010), ![NUMPY](http://www.numpy.org/) and ![SCIPY](https://www.scipy.org/) (Van der Walt et. al. 2011) packages.

[Download OAT](http://www.freewat.eu/)


##Summary

The primary goal of my project was to create `OAT(Data analysis and statistics)` extension in RESTFull Web api and `OAT extension` having data analysis and statistical tools for `istSOS` which is be used to automate the creation of statisticate documents using OAT library and harvesting the data from an istSOS server.

[Data analysis and statistics tools suit commits](https://github.com/rahulworld/Data-analysis/commits/master)

![Implemented OAT methods](https://github.com/rahulworld/Data-analysis/blob/master/examples/README.md)

![OAT Extension](images/quality1.png)


##Tools Used

1. [Pandas](http://pandas.pydata.org/)
2. [NUMPY](http://www.numpy.org/)
3. [SCIPY](https://www.scipy.org/)
4. [d3.js](https://github.com/ruby-prof/ruby-prof)

#Challenges
1. Understanding istSOS structure and OAT package
2. Working with extjs tools in a concurrent environment.
3. Developing consistent suits.

# Scope for future improvements
1. fuctionality add sensor through (CSV, istSOS, Raw)data in `Add sensor name` GUI in `OAT extenstion`.
![Add sensor name](images/addSensorName.png)
2. fuctionality add in `Mangae sensor`.
3. functionalty add in `Compare sensor`.

# Commits

###Data analysis and statistics tool suit Pool
[Removed redundant code, improves performance by upto 3 times](https://github.com/prathmeshranaut/celluloid-pool/commit/b4e42515cfe6095372ce436fd9a2a991b7f3ea5e)

###Celluloid

[Fixed issues with RuboCop](https://github.com/prathmeshranaut/celluloid/commit/8b0ebefaece96d4d00593c7ffca2d30d3d1b2dc8)

[Added comments to the pool benchmark](https://github.com/prathmeshranaut/celluloid/commit/8575b64d75416c39779d075ef51ed9c987d2f3f4)

[updated the results of the pool benchmark](https://github.com/prathmeshranaut/celluloid/commit/fb795163aa035ff8f29419f9134403555bbd6401)

[Updated pool benchmark code](https://github.com/prathmeshranaut/celluloid/commit/c5e50e28437c87079079051ad21d19e8abe5e70d)

[Added Mailbox benchmark](https://github.com/prathmeshranaut/celluloid/commit/1f185b3fbee9827bd9149d1f0b8741529aa24dc2)

[Benchmarking various pool sizes](https://github.com/prathmeshranaut/celluloid/commit/9d888c303502d2cfbb1ca449180e7d076e3057fb)

[Added Async countdown latch benchmark](https://github.com/prathmeshranaut/celluloid/commit/72787ac19d963c77e5d5cdd30bb2a6e4fd4ef910)

[Added results for ring benchmark](https://github.com/prathmeshranaut/celluloid/commit/792b50c500e01fc475da2cdb1aae2676b11d3851)

[Added results for actor benchmarks](https://github.com/prathmeshranaut/celluloid/commit/d954074714ac93321a13673ddc221920c1956887)

[Added benchmark results in the future benchmark results](https://github.com/prathmeshranaut/celluloid/commit/94811fe9a74b4ff4a7f901be9669e895b3a81b5e)

[Added Async Spawn benchmark](https://github.com/prathmeshranaut/celluloid/commit/92d19d38e4db1ad3465e74ad1f6bdb5cdf058d50)

[Added benchmark for futures](https://github.com/prathmeshranaut/celluloid/commit/bbe55e21999043392c3191de22b02892391d022a)

[Fixed Actor test](https://github.com/prathmeshranaut/celluloid/commit/94cacc6bb0d86f6426e02f46200af6f27a321589)

[Re-Added spec helper](https://github.com/prathmeshranaut/celluloid/commit/dec2e0a5239c2a1a15d2ceade4c5c8fc3bd86ac8)

[Converted all the fail exceptinos to raise for convention and testing](https://github.com/prathmeshranaut/celluloid/commit/b6e99e2a639034602d0a92e85de8b301c6ece1ba)

[Added test for mailbox example](https://github.com/prathmeshranaut/celluloid/commit/69eb36779170904c82d83069111e5de78f9453d9)

[Instruction for cloning Celluloid via github](https://github.com/prathmeshranaut/celluloid/commit/f403f59a5b2a671537bfa3af5a4069e3b0ac8ce5)

[Merge branch 'multiplex' of https://github.com/celluloid/celluloid](https://github.com/prathmeshranaut/celluloid/commit/d96ea3699d0a
---41583ade963a512b81a7f31a3dd1)

##Other Links
* [Commits](https://github.com/rahulworld/Data-analysis/commits/master)
* [Cloning Repo.](https://github.com/istSOS/istsos2)
* [Blog](https://rahulworld.github.io/GSoC.html)
* [Images and documentation](https://github.com/rahulworld/Data-analysis/blob/master/examples/README.md)
* [istSOS Web](http://istsos.org/)
* [Github](https://github.com/rahulworld)
* [Wiki](https://wiki.osgeo.org/wiki/GSoC_17:_istSOS-Data_analysis_and_statistical_tools_suite)
* [email](rahulnitsxr@gmail.com)