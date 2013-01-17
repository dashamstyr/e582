#new 2012/Nov/02
from __future__ import division
#see http://pysclint.sourceforge.net/pyhdf/
import matplotlib
import pyhdf.SD
import numpy as np
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
plt.switch_backend('Agg')
import glob, sys, os
import site
#
# add the current directory to the module
# search path
#
cwd=os.getcwd()
site.addsitedir(cwd)
from modismeta import parseMeta
from orient import orient


from binit import binit

if __name__=="__main__":

    #
    # new -- make a folder to hold plots, if one
    # doesn't already exist
    #
    if not os.path.isdir('plots'):
        try:
            os.mkdir('plots')
        except:
            print 'tried and filed to create "plots" directory'
            sys.exit(1)

    max_rows=300
    max_cols=200
    #get the name of files ending in hdf
    the_files=glob.glob('MOD03*275*hdf')
    #take the first one (only one file fits this description)
    the_file=the_files[0]

    # here's the header information
    print parseMeta(the_file)

    #get the full latitude and longitude arrays
    sdgeom=pyhdf.SD.SD(the_file)
    fullLats=sdgeom.select('Latitude')
    fullLats=fullLats.get()
    fullLons=sdgeom.select('Longitude')
    fullLons=fullLons.get()
    sdgeom.end()

    the_files=glob.glob('MOD*21KM*275*hdf')
    the_file=the_files[0]
    sdrad=pyhdf.SD.SD(the_file)
    longWave=sdrad.select('EV_1KM_Emissive')
    #
    # this array will be 16 x 2040 x 1354
    #  16 wavelengths
    #  2040 along-track scan lines
    #  1354 across-track pixels in each scan line
    #  see http://gis.cri.fmach.it/modis-sensor/ for channel wavelengths
    #
    allRadiances=longWave.get()
    #
    # find the index for channel 31 (it's 10, i.e. channel 31 is
    # the 11th channel)
    #
    theChans=longWave.attributes()['band_names']
    band_names=theChans.split(',')
    index31=band_names.index('31')
    #
    #  get the radiances as 16 bit integers
    #
    chan31=allRadiances[index31,:,:]
    #
    # apply scale and offset to convert to 64 bit floats
    #
    scale31=longWave.attributes()['radiance_scales'][index31]
    offset31=longWave.attributes()['radiance_offsets'][index31]
    chan31 = scale31 * (chan31 - offset31)

    #
    # flip the array if necessary so col[0] is west and row[0] 
    # is south
    #
    fullLats,fullLons,chan31=orient(fullLats,fullLons,chan31)


    #
    # take a small subset to speed things up
    #
    partLats=fullLats[:max_rows,:max_cols]
    partLons=fullLons[:max_rows,:max_cols]
    partChan31=chan31[:max_rows,:max_cols]


    
    fig0a,axis0a=plt.subplots(1,1)
    im=axis0a.contourf(partLats)
    cb=plt.colorbar(im)
    the_label=cb.ax.set_ylabel('latitude (deg)',rotation=270)
    axis0a.set_title('partial scene latitude')
    fig0a.savefig('plots/partial_lat.png')
    
    fig0b,axis0b=plt.subplots(1,1)
    im=axis0b.contourf(partLons)
    cb=plt.colorbar(im)
    the_label=cb.ax.set_ylabel('longitude (deg)',rotation=270)
    axis0b.set_title('partial scene longitude')
    fig0b.savefig('plots/partial_lon.png')
    
    numlatbins=60
    numlonbins=120
    bin_lats=binit(-30.5,-27,numlatbins,-999,-888)
    bin_lons=binit(-101,-94,numlonbins,-999,-888)

    #
    # use ravel() to turn 2-d arrays into 1-d arrays
    #
    lat_count,lat_index,lowlats,highlats=bin_lats.do_bins(partLats.ravel())    
    lon_count,lon_index,lowlons,highlons=bin_lons.do_bins(partLons.ravel())    
    #
    # check to make sure that the binit histogram agrees with matplotlib hist
    #
    fig1,axes=plt.subplots(2,1)
    lat_centers=bin_lats.get_centers()
    my_edges=bin_lats.get_edges()
    axes[0].hist(partLats.ravel(),bins=my_edges)
    axes[0].plot(lat_centers,lat_count,'r.',markersize=10)
    axes[0].set_title('latitudes from binit (red) and hist (blue)')
    lon_centers=bin_lons.get_centers()
    my_edges=bin_lons.get_edges()
    axes[1].hist(partLons.ravel(),bins=my_edges)
    axes[1].plot(lon_centers,lon_count,'r.',markersize=10)
    axes[1].set_title('longitudes from binit (red) and hist (blue)')
    fig1.savefig('plots/hist.png')
    
    out_grid=np.zeros([bin_lats.numbins,bin_lons.numbins])
    for index in range(lat_index.size):
        lat_bin=lat_index[index]
        lon_bin=lon_index[index]
        if lat_bin < 0 or lon_bin < 0:
            continue
        out_grid[lat_bin,lon_bin]+=1
  
    fig2,axis2=plt.subplots(1,1)
    im=axis2.contourf(lon_centers,lat_centers,out_grid,levels=[0,1,2,3,4,5],extend='max')
    cb=plt.colorbar(im)
    the_label=cb.ax.set_ylabel('number of pixels in grid cell',rotation=270)
    regLon,regLat=np.meshgrid(lon_centers,lat_centers)
    axis2.plot(regLon,regLat,'r.',markersize=8)
    axis2.set_title('coverage map')
    fig2.savefig('plots/coverage.png')
    

    fig0,axis0=plt.subplots(1,1)
    im=axis0.contourf(chan31)
    cb=plt.colorbar(im)
    the_label=cb.ax.set_ylabel('radiance ($W\,m^{-2}\,{\mu m}^{-1}\,sr^{-1}$)',rotation=270)
    axis0.set_title('channel 31 full scene')
    fig0.savefig('plots/channel31_full.png')
    
    fig3,axis3=plt.subplots(1,1)
    im=axis3.contourf(partChan31,extend='both')
    cb=plt.colorbar(im)
    the_label=cb.ax.set_ylabel('radiance ($W\,m^{-2}\,{\mu m}^{-1}\,sr^{-1}$)',rotation=270)
    axis3.set_title('MODIS channel 31 radiance (partial scene)')
    fig3.savefig('plots/channel31_partial.png')
    #
    # for plotting lon is x (row) and lat is y (col)
    #
    out_vals=np.empty([bin_lats.numbins,bin_lons.numbins],dtype=np.object)
    for row in range(bin_lats.numbins):
        for col in range(bin_lons.numbins):
            out_vals[row,col]=list()

    for data_index in range(lat_index.size):
        grid_row=lat_index[data_index]
        grid_col=lon_index[data_index]
        if grid_row < 0 or grid_col < 0:
            continue
        out_vals[grid_row,grid_col].append(data_index)

    rad_grid=np.empty_like(out_vals,dtype=np.float)
    lat_grid=np.empty_like(out_vals,dtype=np.float)
    lon_grid=np.empty_like(out_vals,dtype=np.float)
    rows,cols=rad_grid.shape
    flat_chan31=partChan31.ravel()
    for the_row in range(rows):
        for the_col in range(cols):
            rad_list=out_vals[the_row,the_col]
            if len(rad_list)==0:
                rad_grid[the_row,the_col]=np.nan
                lat_grid[the_row,the_col]=np.nan
                lon_grid[the_row,the_col]=np.nan
            else:
                try:
                    rad_vals=np.take(flat_chan31,rad_list)
                    lat_vals=np.take(partLats.ravel(),rad_list)
                    lon_vals=np.take(partLons.ravel(),rad_list)
                    rad_grid[the_row,the_col]=np.mean(rad_vals)
                    lat_grid[the_row,the_col]=np.mean(lat_vals)                    
                    lon_grid[the_row,the_col]=np.mean(lon_vals)                    
                except IndexError:
                    print "oops: ",rad_list

    fig4,axis4=plt.subplots(1,1)
    im=axis4.contourf(lon_centers,lat_centers,rad_grid,extend='both')
    cb=plt.colorbar(im)
    the_label=cb.ax.set_ylabel('radiances ($W\,m^{-2}\,{\mu m}^{-1}\,sr^{-1}$)',rotation=270)
    axis4.set_title('MODIS channel 31 radiances (lat/lon binned')
    fig4.savefig('plots/chan31_binned.png')

    fig5,axis5=plt.subplots(1,1)
    im=axis5.contourf(lon_centers,lat_centers,lat_grid,extend='both')
    cb=plt.colorbar(im)
    the_label=cb.ax.set_ylabel('latitude (degrees)',rotation=270)
    axis5.set_title('binned latitude')
    fig5.savefig('plots/lat_binned.png')

    fig6,axis6=plt.subplots(1,1)
    im=axis6.contourf(lon_centers,lat_centers,lon_grid,extend='both')
    cb=plt.colorbar(im)
    the_label=cb.ax.set_ylabel('latitude (degrees)',rotation=270)
    axis6.set_title('binned longitude')
    fig6.savefig('plots/lon_binned.png')
