#!/home/ZhiLi/env/bin/python
import numpy as np
import configparser
import os
import pandas as pd
from glob import glob

def get_DREAM(fac):
    if fac<1000:
        return 10000
    elif 1000<fac<10000:
        return 8000
    else: return 5000

gauges= pd.read_csv('../USGS_gauges/gauge_meta.csv',index_col=[0], dtype={'STAID':str})
gauges= gauges[gauges.DRAIN_SQKM>100]
gauges= gauges[gauges.CLASS=='Ref']
gauges= gauges.sort_values(by='DRAIN_SQKM')
obs_id= [fname.split('/')[-1].split('.')[0] for fname in glob('../USGS_gauges/*.csv')]
for i in range(len(gauges)):
    gauge_id= gauges.STAID.iloc[i]
    if gauge_id in obs_id:
        os.system('mkdir cali/%s'%gauge_id)
        config = configparser.ConfigParser()
        config.read('control_phys.txt')
        # execute cali----
        config['Gauge 1']['cellx']= str(int(gauges.col.iloc[i]))
        config['Gauge 1']['celly']= str(int(gauges.row.iloc[i]))
        config['Gauge 1']['OBS']= '/hydros/ZhiLi/USGS_gauges/%s.csv'%(gauge_id)
        config['Gauge 1']['BASINAREA']= str(gauges.DRAIN_SQKM.iloc[i])
        config['Task cali']['output']='/hydros/ZhiLi/EF-parameters/cali/%s'%gauge_id
        config['Task simu']['output']='/hydros/ZhiLi/EF-parameters/cali/%s'%gauge_id
        config['CrestphysCaliParams crestparaCal']['DREAM_NDRAW']= str(get_DREAM(gauges.DRAIN_SQKM.iloc[i]))
        with open('_control.txt', 'w') as configfile:
               config.write(configfile,False)
        print('calibrating %s'%gauges.STAID.iloc[i])
        # os.system('/home/ZhiLi/EF5/bin/ef5 _control.txt > /dev/null')
        #execute simu----
        ## update parameters
        results_parser = configparser.RawConfigParser()
        with open('/hydros/ZhiLi/EF-parameters/cali/%s'%gauge_id+'/cali_dream.1.crestphys.csv') as f:
            contents= f.readlines()
            i_config= [i for i,line in enumerate(contents) if line=='[WaterBalance]\n']
            file_content = ''.join(contents[i_config[0]:])
            # file_content = ''.join(f.readlines()[int(get_DREAM(gauges.DRAIN_SQKM.iloc[i]))-2:])
        results_parser.read_string(file_content)
        config['CrestphysParamSet crestpara']['wm']= results_parser['WaterBalance']['wm']
        config['CrestphysParamSet crestpara']['im']= results_parser['WaterBalance']['im']
        config['CrestphysParamSet crestpara']['fc']= results_parser['WaterBalance']['fc']
        config['CrestphysParamSet crestpara']['b']= results_parser['WaterBalance']['b']
        config['CrestphysParamSet crestpara']['ke']= results_parser['WaterBalance']['ke']
        config['CrestphysParamSet crestpara']['hmaxaq']= results_parser['WaterBalance']['hmaxaq']
        config['CrestphysParamSet crestpara']['gwc']= results_parser['WaterBalance']['gwc']
        config['CrestphysParamSet crestpara']['gwe']= results_parser['WaterBalance']['gwe']

        config['KWParamSet routpara']['alpha']= results_parser['Routing']['alpha']
        config['KWParamSet routpara']['alpha0']= results_parser['Routing']['alpha0']
        config['KWParamSet routpara']['beta']= results_parser['Routing']['beta']
        config['KWParamSet routpara']['leaki']= results_parser['Routing']['leaki']
        config['KWParamSet routpara']['under']= results_parser['Routing']['under']
        config['KWParamSet routpara']['th']= results_parser['Routing']['th']
        config['Execute']['task']='simu'
        with open('_control.txt', 'w') as configfile:
               config.write(configfile,False)
        print('evaluating %s'%gauges.STAID.iloc[i])
        os.system('/home/ZhiLi/EF5/bin/ef5 _control.txt > /dev/null')
        os.system('rm cali/%s/califorcings.bin'%gauge_id)
        print('Completing gauge %s'%gauge_id)
    break
