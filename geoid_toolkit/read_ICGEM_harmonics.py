#!/usr/bin/env python
u"""
read_ICGEM_harmonics.py
Written by Tyler Sutterley (07/2020)
Reads the coefficients for a given gravity model file
Particular cases for SWARM, COST-G and GRAZ data

GFZ International Centre for Global Earth Models (ICGEM)
    http://icgem.gfz-potsdam.de/

GRAZ: https://www.tugraz.at/institute/ifg/downloads/gravity-field-models
data can be downloaded from this ftp server:
    ftp://ftp.tugraz.at/outgoing/ITSG/GRACE/

SWARM: https://earth.esa.int/eogateway/missions/swarm
data can be downloaded from this ftp server:
    ftp://swarm-diss.eo.esa.int/Level2longterm/EGF/

COST-G: https://cost-g.org/
data can be downloaded from the ICGEM website

INPUTS:
    model_file: full path to *.gfc file with spherical harmonic coefficients

OPTIONS:
    LMAX: maximum degree and order of output spherical harmonic coefficients
    TIDE: tide system of output geoid
        http://mitgcm.org/~mlosch/geoidcookbook/node9.html
        tide_free: no permanent direct and indirect tidal potentials
            this is the default (leaving the model as is)
        mean_tide: restores permanent tidal potentials (direct and indirect)
        zero_tide: restores permanent direct tidal potential
    FLAG: string denoting data lines

OUTPUTS:
    clm: cosine spherical harmonics of input data
    slm: sine spherical harmonics of input data
    eclm: cosine spherical harmonic standard deviations of type errors
    eslm: sine spherical harmonic standard deviations of type errors
    modelname: name of the gravity model
    earth_gravity_constant: GM constant of the Earth for the gravity model
    radius: semi-major axis of the Earth for the gravity model
    max_degree: maximum degree and order for the gravity model
    errors: error type of the gravity model
    norm: normalization of the spherical harmonics
    tide_system: tide system of gravity model (mean_tide, zero_tide, tide_free)

PYTHON DEPENDENCIES:
    numpy: Scientific Computing Tools For Python
        https://numpy.org
        https://numpy.org/doc/stable/user/numpy-for-matlab-users.html

PROGRAM DEPENDENCIES:
    calculate_tidal_offset.py: calculates the C20 offset for a tidal system

UPDATE HISTORY:
    Updated 05/2021: Add GRAZ/SWARM/COST-G ICGEM file
    Updated 03/2021: made degree of truncation LMAX a keyword argument
    Updated 07/2020: added function docstrings
    Updated 07/2019: split read and wrapper funciton into separate files
    Updated 07/2017: include parameters to change the tide system
    Written 12/2015
"""
import os
import re
import numpy as np
from geoid_toolkit.calculate_tidal_offset import calculate_tidal_offset

#-- PURPOSE: read spherical harmonic coefficients of a gravity model
def read_ICGEM_harmonics(model_file, LMAX=None, TIDE='tide_free', FLAG='gfc'):
    """
    Extract gravity model spherical harmonics from GFZ/GRAZ/SWARM/COST-G ICGEM gfc files
    In case of GRAZ/SWARM/COST-G, save also the date of the series

    Arguments
    ---------
    model_file: full path to *.gfc file with spherical harmonic coefficients
    LMAX: maximum degree and order of output spherical harmonic coefficients

    Keyword arguments
    -----------------
    TIDE: tide system of output geoid
    FLAG: string denoting data lines

    Returns
    -------
    clm: cosine spherical harmonics of input data
    slm: sine spherical harmonics of input data
    eclm: cosine spherical harmonic standard deviations of type errors
    eslm: sine spherical harmonic standard deviations of type errors
    modelname: name of the gravity model
    earth_gravity_constant: GM constant of the Earth for gravity model
    radius: semi-major axis of the Earth for gravity model
    max_degree: maximum degree and order for gravity model
    errors: error type of the gravity model
    norm: normalization of the spherical harmonics
    tide_system: tide system of gravity model

    Special case for gfc files from GRAZ, SWARM and COST-G
    time: mid-month date in decimal form
    start: Julian dates of the start date
    end: Julian dates of the start date
    """
    # -- python dictionary with model input and headers
    model_input = {}

    if 'ITSG' in model_file:
        # -- compile numerical expression operator for parameters from files
        # -- GRAZ: Institute of Geodesy from GRAZ University of Technology
        regex_pattern = (r'(.*?)-({0})_(.*?)_(\d+)-(\d+)'
                         r'(\.gz|\.gfc|\.txt)').format(r'Grace_operational|Grace2018')
        rx = re.compile(regex_pattern, re.VERBOSE)
        # -- extract parameters from input filename
        PFX, SAT, trunc, year, month, SFX = rx.findall(os.path.basename(model_file)).pop()

        # -- convert string to integer
        year, month = int(year), int(month)

    elif 'SW_' in model_file:
        # -- compile numerical expression operator for parameters from files
        # -- SWARM: data from SWARM satellite
        regex_pattern = (r'({0})_(.*?)_(EGF_SHA_2)__(.*?)_(.*?)_(.*?)'
                         r'(\.gz|\.gfc|\.txt)').format(r'SW')
        rx = re.compile(regex_pattern, re.VERBOSE)
        SAT, tmp, PROD, start_date, end_date, RL, SFX = rx.findall(os.path.basename(model_file)).pop()

        # -- convert string to integer
        year = int(start_date[:4])
        month = int(start_date[4:6])

    elif 'COSTG' in model_file:
        # -- compile numerical expression operator for parameters from files
        # -- COST-G: Combine product of the IGFS
        regex_pattern = (r'(.*?)-2_(\d+)-(\d+)_(.*?)_({0})_(.*?)_(\d+)(.*?)'
                         r'(\.gz|\.gfc|\.txt)?$').format('COSTG')
        rx = re.compile(regex_pattern, re.VERBOSE)
        PFX, SD, ED, N, PRC, F1, DRL, F2, SFX = rx.findall(os.path.basename(model_file)).pop()

        start_yr = np.float(SD[:4])
        end_yr = np.float(ED[:4])
        start_day = np.float(SD[4:])
        end_day = np.float(ED[4:])

    if 'ITSG' in model_file or 'SW_' in model_file:
        # -- calculate mid-month date taking into account if measurements are
        # -- on different years
        if (year % 4) == 0:  # -- Leap Year
            dpy = 366.0
            dpm = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        else:  # -- Standard Year
            dpy = 365.0
            dpm = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

        start_day = np.sum(dpm[:month - 1]) + 1
        end_day = np.sum(dpm[:month])

        # -- Calculation of Mid-month value
        mid_day = np.mean([start_day, end_day])
        # -- Calculating the mid-month date in decimal form
        model_input['time'] = year + mid_day / dpy
        # -- Calculating the Julian dates of the start and end date
        model_input['start'] = np.float(367.0 * year - np.floor(7.0 * year / 4.0) -
                                        np.floor(3.0 * (np.floor((year - 8.0 / 7.0) / 100.0) + 1.0) / 4.0) +
                                        np.floor(275.0 / 9.0) + start_day + 1721028.5)
        model_input['end'] = np.float(367.0 * year - np.floor(7.0 * year / 4.0) -
                                      np.floor(3.0 * (np.floor((year - 8.0 / 7.0) / 100.0) + 1.0) / 4.0) +
                                      np.floor(275.0 / 9.0) + end_day + 1721028.5)

    elif 'COSTG' in model_file:
        # -- calculate mid-month date taking into account if measurements are
        # -- on different years
        if (start_yr % 4) == 0:  # -- Leap Year
            dpy = 366.0
        else:  # -- Standard Year
            dpy = 365.0

        # -- For data that crosses years (end_yr - start_yr should be at most 1)
        end_cyclic = ((end_yr - start_yr) * dpy + end_day)
        # -- Calculate mid-month value
        mid_day = np.mean([start_day, end_cyclic])

        # -- Calculating the mid-month date in decimal form
        model_input['time'] = start_yr + mid_day / dpy
        # -- Calculating the Julian dates of the start and end date
        model_input['start'] = np.float(367.0 * start_yr - np.floor(7.0 * start_yr / 4.0) -
                                        np.floor(3.0 * (np.floor((start_yr - 8.0 / 7.0) / 100.0) + 1.0) / 4.0) +
                                        np.floor(275.0 / 9.0) + start_day + 1721028.5)
        model_input['end'] = np.float(367.0 * end_yr - np.floor(7.0 * end_yr / 4.0) -
                                      np.floor(3.0 * (np.floor((end_yr - 8.0 / 7.0) / 100.0) + 1.0) / 4.0) +
                                      np.floor(275.0 / 9.0) + end_day + 1721028.5)

    #-- read input data
    with open(os.path.expanduser(model_file),'r') as f:
        file_contents = f.read().splitlines()
    #-- extract parameters from header
    header_parameters = ['modelname','earth_gravity_constant','radius',
        'max_degree','errors','norm','tide_system']
    parameters_regex = '(' + '|'.join(header_parameters) + ')'
    header = [l for l in file_contents if re.match(parameters_regex,l)]
    for line in header:
        #-- split the line into individual components
        line_contents = line.split()
        model_input[line_contents[0]] = line_contents[1]
    #-- set degree of truncation from model if not presently set
    LMAX = np.int(model_input['max_degree']) if not LMAX else LMAX
    #-- allocate for each Coefficient
    model_input['clm'] = np.zeros((LMAX+1,LMAX+1))
    model_input['slm'] = np.zeros((LMAX+1,LMAX+1))
    if not('SW_' in model_file): #-- SWARM doesn't contain errors
        model_input['eclm'] = np.zeros((LMAX+1,LMAX+1))
        model_input['eslm'] = np.zeros((LMAX+1,LMAX+1))
    #-- reduce file_contents to input data using data marker flag
    input_data = [l for l in file_contents if re.match(FLAG,l)]
    #-- for each line of data in the gravity file
    for line in input_data:
        #-- split the line into individual components replacing fortran d
        line_contents = re.sub('d','e',line,flags=re.IGNORECASE).split()
        #-- degree and order for the line
        l1 = np.int(line_contents[1])
        m1 = np.int(line_contents[2])
        #-- if degree and order are below the truncation limits
        if ((l1 <= LMAX) and (m1 <= LMAX)):
            model_input['clm'][l1,m1] = np.float(line_contents[3])
            model_input['slm'][l1,m1] = np.float(line_contents[4])
            if not ('SW_' in model_file):  # -- SWARM doesn't contain errors
                model_input['eclm'][l1,m1] = np.float(line_contents[5])
                model_input['eslm'][l1,m1] = np.float(line_contents[6])
    #-- calculate the tidal offset if changing the tide system
    if TIDE in ('mean_tide','zero_tide'):
        model_input['tide_system'] = TIDE
        GM = np.float(model_input['earth_gravity_constant'])
        R = np.float(model_input['radius'])
        model_input['clm'][2,0] += calculate_tidal_offset(TIDE,GM,R,'WGS84')
    #-- return the spherical harmonics and parameters
    return model_input
