# StreaMD: a tool to perform high-throughput automated molecular dynamics simulations

## installation
*Source: https://valdes-tresanco-ms.github.io/gmx_MMPBSA/installation/*

We recommend to install the package using `conda` and `mamba`. To use exclusively `conda` one can simply replace `mamba` calls with `conda`.
```
conda install -n base -c conda-forge mamba

conda create -n md python=3.9 -y -q
conda activate md

mamba install -c conda-forge mpi4py=3.1.3 ambertools=21.12 compilers=1.2.0 gromacs==2022.4 rdkit dask distributed -y -q

python -m pip install git+https://github.com/Valdes-Tresanco-MS/ParmEd.git@v3.4
python -m pip install gmx_MMPBSA

pip install paramiko asyncssh prolif

pip install git+https://github.com/ci-lab-cz/md-scripts.git
```

## **Description**
#### **Fully automatic pipeline for molecular dynamics**

#### Features:  
- supports simulation for different systems:  
    - Protein in Water;  
    - Protein - Ligand;  
    - Protein - Cofactor (multiple);  
    - Protein - Ligand - Cofactor (multiple);  
    
- supports of simulations of boron-containing molecules using Gaussian Software
- supports distributed computing using dask library
- supports of running of parallel simulations on multiple servers
- supports to extend time of MD simulations 
- supports to continue of interrupted MD simulation
- interrupted MD preparation can be restarted by invoking the same command
- implemented tools for end-state free energy calculations (gmx_MMPBSA) and Protein-Ligand Interaction analysis (ProLIF)

### **USAGE**
```
run_md -h
usage: run_md [-h] [-p FILENAME] [-d WDIR] [-l FILENAME] [--cofactor FILENAME] [--clean_previous_md] [--hostfile FILENAME] [-c INTEGER] [--topol topol.top]
              [--topol_itp topol_chainA.itp topol_chainB.itp [topol_chainA.itp topol_chainB.itp ...]] [--posre posre.itp [posre.itp ...]] [--md_time ns] [--npt_time ps] [--nvt_time ps]
              [--not_clean_log_files] [--tpr FILENAME] [--cpt FILENAME] [--xtc FILENAME] [--wdir_to_continue DIRNAME [DIRNAME ...]] [--deffnm preffix for md files]
              [--activate_gaussian module load Gaussian/09-d01] [--gaussian_exe g09 or /apps/all/Gaussian/09-d01/g09/g09]

Run or continue MD simulation. Allowed systems: Protein, Protein-Ligand, Protein-Cofactors(multiple), Protein-Ligand-Cofactors(multiple)

optional arguments:
  -h, --help            show this help message and exit
  -p FILENAME, --protein FILENAME
                        input file of protein. Supported formats: *.pdb or gro
  -d WDIR, --wdir WDIR  Working directory. If not set the current directory will be used.
  -l FILENAME, --ligand FILENAME
                        input file with compound. Supported formats: *.mol or sdf
  --cofactor FILENAME   input file with compound. Supported formats: *.mol or sdf
  --clean_previous_md   remove a production MD simulation directory if it exists to re-initialize production MD setup
  --hostfile FILENAME   text file with addresses of nodes of dask SSH cluster. The most typical, it can be passed as $PBS_NODEFILE variable from inside a PBS script. The first line in this file will be
                        the address of the scheduler running on the standard port 8786. If omitted, calculations will run on a single machine as usual.
  -c INTEGER, --ncpu INTEGER
                        number of CPU per server. Use all cpus by default.
  --topol topol.top     topology file (required if a gro-file is provided for the protein).All output files obtained from gmx2pdb should preserve the original names
  --topol_itp topol_chainA.itp topol_chainB.itp [topol_chainA.itp topol_chainB.itp ...]
                        Itp files for individual protein chains (required if a gro-file is provided for the protein).All output files obtained from gmx2pdb should preserve the original names
  --posre posre.itp [posre.itp ...]
                        posre file(s) (required if a gro-file is provided for the protein).All output files obtained from gmx2pdb should preserve the original names
  --md_time ns          time of MD simulation in ns
  --npt_time ps         time of NPT equilibration in ps
  --nvt_time ps         time of NVT equilibration in ps
  --not_clean_log_files
                        Not to remove all backups of md files
  --tpr FILENAME        tpr file from the previous MD simulation
  --cpt FILENAME        cpt file from previous simulation
  --xtc FILENAME        xtc file from previous simulation
  --wdir_to_continue DIRNAME [DIRNAME ...]
                        single or multiple directories for the previous simulations. Use to extend or continue the simulation. ' Should consist of: tpr, cpt, xtc files
  --deffnm preffix for md files
                        preffix for the previous md files. Use to extend or continue the simulation. Only if wdir_to_continue is used. Use if each --tpr, --cpt, --xtc arguments are not set up. Files
                        deffnm.tpr, deffnm.cpt, deffnm.xtc will be used from wdir_to_continue
  --activate_gaussian module load Gaussian/09-d01
                        string that load gaussian module if necessary
  --gaussian_exe g09 or /apps/all/Gaussian/09-d01/g09/g09
                        path to gaussian executable or alias. Requred to run preparation of boron-containing compounds.

```

### **Examples**
! Before run MD simulation it is important to prepare protein by yourself to make sure you simulate correct system.
#### 1) Target Preparation:  
*Manual preparation:*
- **Fill missing residues and loops**  

*Using Chimera:*   

``Tools -> Sequence -> Structure -> Modeller (loops/refinement)``  
``Tools -> Structure Editing -> Dock Prep ``
* **Explicit water molecules as well as cofactors from a crystal structure can be removed, or if necessarily retained manually;**

* **Remove co-crystallizated ligands;**

* **Add hydrogens based on protonation states.**
  * Check states of histidines and put proper aliases HIE, HID or HIP instead of HIS (otherwise protonation can be distorted during MD preparation stage)  

*type into Chimera cmd:*
```
setattr r type HID :HIS@HD1,DD1,TD1,HND
setattr r type HIP :HID@HE2,DE2,TE2
setattr r type HIE :HIS@HE2
```

#### 2) Docking procedure
Required to obtain relevant poses of the ligand if need
* **Perform docking procedure**  
https://github.com/ci-lab-cz/easydock

#### Run molecular dynamics simulation
``` source activate gmxMMPBSA ```  
 
**Run simulation for different sytems:**
- Protein in Water
```
run_md -p protein_H_HIS.pdb --md_time 0.1 --nvt_time 100 --npt_time 100 --ncpu 128 
```

- Protein - Ligand
```
run_md -p protein_H_HIS.pdb -l ligand.mol --md_time 0.1 --nvt_time 100 --npt_time 100 --ncpu 128 
```

- Protein - Cofactor
All molecules should present in simulated system, so any problem with preparation of cofactors will interrupt the program. 
```
run_md -p protein_H_HIS.pdb --cofactor cofactors.sdf --md_time 0.1 --nvt_time 100 --npt_time 100 --ncpu 128 

```

**To run simulations with boron-containing compounds**  
*Gaussian Software* should be available.  
Gaussian optimization and charge calculation will be run only for molecules with boron atoms, other molecules will be processed by regular procedure by Antechamber.
If Gaussian cannot be load boron-containing molecules will be skipped.  
Any --ligand or --cofactor files can consist of boron-containing compounds
```
run_md -p protein_H_HIS.pdb -l molecules.sdf --cofactor cofactors.sdf --md_time 0.1 --npt_time 10 --nvt_time 10 --activate_gaussian "module load Gaussian/09-d01" --gaussian_exe g09 --ncpu 128

```

**To run simulations using multiple servers**
```
run_md -p protein_H_HIS.pdb -l molecules.sdf --cofactor cofactors.sdf --md_time 0.1 --npt_time 10 --nvt_time 10 --hostfile $PBS_NODEFILE --ncpu 128
```

**To extend the simulation**
```
run_md --wdir_to_continue md_preparation/md_files/protein_H_HIS_ligand_1/ md_preparation/md_files/protein_H_HIS_ligand_*/ --md_time 0.2 --deffnm md_out
```
you can continue your simulation unlimited times just use previous extended deffnm OR tpr, cpt and xtc arguments 
```
run_md --wdir_to_continue md_preparation/md_files/protein_H_HIS_ligand_1/  --md_time 0.3 --deffnm md_out_0.2
```
or 
```
run_md --wdir_to_continue md_preparation/md_files/protein_H_HIS_ligand_1/  --md_time 0.3 --tpr md_preparation/md_files/protein_H_HIS_ligand_1/md_out_0.2.tpr --cpt md_preparation/md_files/protein_H_HIS_ligand_1/md_out_0.2.cpt --xtc md_preparation/md_files/protein_H_HIS_ligand_1/md_out_0.2.xtc
```
  
**Output**   
*each run creates in the working directory (or in the current directory if wdir argument was not set up):*
 1) a unique streaMD log file which name contains name of the protein, ligand file, cofactor file and time of run.  
 log_*protein-fname*\_*ligand-fname*\_*cofactor-fname*\_*start-time*.log  
 Contains important information/warnings/errors about the main program run.
 2) a unique bash log file.  
 streamd_bash_*protein-fname*\_*ligand-fname*\_*cofactor-fname*\_*start-time*.log  
 Contains stdout from Gromacs and Antechamber.  
 
will be created the next folders:
```
md_files/
- md_files/md_preparation/
 -- md_files/md_preparation/protein/
 -- md_files/md_preparation/ligands/
 -- md_files/md_preparation/cofactors/
- md_files/md_run/
```

```
md_files/md_preparation/protein/:
protein.gro  posre.itp  topol.top

OR for multiple chain protein:
md_preparation/protein/:
protein.gro 
topol.top
posre_Protein_chain_A.itp    
posre_Protein_chain_B.itp  
topol_Protein_chain_A.itp
topol_Protein_chain_B.itp
```

```
md_files/md_preparation/ligands/:
all_resid.txt

ligand_1/
ligand_1.frcmod  ligand_1.lib     ligand_1.top        sqm.in
ligand_1.gro     ligand_1.mol     leap.log            sqm.out
ligand_1.inpcrd  ligand_1.mol2    posre_ligand_1.itp  sqm.pdb
ligand_1.itp     ligand_1.prmtop  resid.txt           tleap.in

ligand_2/
..
```

```
md_files/md_preparation/cofactors/:
all_resid.txt

cofactor_1/
cofactor_1.frcmod  cofactor_1.lib     cofactor_1.top        sqm.in
cofactor_1.gro     cofactor_1.mol     leap.log              sqm.out
cofactor_1.inpcrd  cofactor_1.mol2    posre_cofactor_1.itp  sqm.pdb
cofactor_1.itp     cofactor_1.prmtop  resid.txt             tleap.in

cofactor_2/
...
```

```
md_files/md_run/md_files/

protein_H_HIS_ligand_1/
ligand_1.itp          density.xvg  em.trr      ions.tpr                md_out.edr         md_out.tpr             npt.cpt  npt.tpr  nvt.log    potential.xvg         rmsd.xvg       temperature.xvg
cofactor_1.itp        em.edr       frame.pdb   md_centermolsnoPBC.xtc  md_out.gro         md_out.xtc             npt.edr  npt.trr  nvt.mdp    pressure.xvg          rmsf.pdb       topol.top
all.itp               em.gro       gyrate.xvg  md_fit.xtc              md_out.log         md_short_forcheck.xtc  npt.gro  nvt.cpt  nvt.tpr    rmsd_cofactor_1.xvg   rmsf.xvg
all_ligand_resid.txt  em.log       index.ndx   md.mdp                  mdout.mdp          minim.mdp              npt.log  nvt.edr  nvt.trr    rmsd_ligand_1.xvg     solv.gro
complex.gro           em.tpr       ions.mdp    md_out.cpt              md_out_noj_noPBC.xtc  newbox.gro          npt.mdp  nvt.gro  posre.itp  rmsd_xtal.xvg         solv_ions.gro

protein_H_HIS_ligand_2/
```
- **MD output files**
```
md_fit.xtc - MD trajectory with removed PBC and fitted into Protein or Protein-Ligand group
md_short_forcheck.xtc - short trajectory to check if simulation was valid
frame.pdb - a frame for topology

```
- **Analysis data**  
```
potential.xvg - m
temperature.xvg
pressure.xvg
density.xvg
rmsd.xvg - rmsd of the protein against minimized structure
rmsd_xtal.xvg - rmsd of the protein against crystal structure
rmsd_cofactor_1.xvg - rmsd of each cofactors
rmsd_ligand_1.xvg - rmsd of the ligand
rmsf.xvg - root mean square fluctuation (RMSF, i.e. standard deviation) of atomic positions in the trajectory
gyrate.xvg - radius of gyration
```
_All analysis results you can visualize with xmgrace:_  
`` for i in *.xvg; do gracebat $i;done `` 

### MM-PBSA/MM-GBSA energy calculation
#### **USAGE**
```
run_gbsa -h
usage: run_gbsa [-h] [--wdir_to_run DIRNAME [DIRNAME ...]] [--topol topol.top] [--tpr md_out.tpr] [--xtc md_fit.xtc] [--index index.ndx] -m mmpbsa.in [-d WDIR] [--out_files OUT_FILES [OUT_FILES ...]]
                   [--hostfile FILENAME] [-c INTEGER] [--deffnm preffix for md files] [--ligand_id UNL] [--clean_previous]

Run MM-GBSA/MM-PBSA calculation using gmx_MMPBSA tool

optional arguments:
  -h, --help            show this help message and exit
  --wdir_to_run DIRNAME [DIRNAME ...]
                        single or multiple directories with simulations. Should consist of: tpr, xtc, ndx files
  --topol topol.top     topol file from the the MD simulation
  --tpr md_out.tpr      tpr file from the MD simulation
  --xtc md_fit.xtc      xtc file of the simulation. Trajectory should have no PBC and be fitted on the Protein_Ligand group
  --index index.ndx     index file from the MD simulation
  -m mmpbsa.in, --mmpbsa mmpbsa.in  MMPBSA input file. If not set up default template will be used.
  -d WDIR, --wdir WDIR  Working directory. If not set the current directory will be used.
  --out_files OUT_FILES [OUT_FILES ...]
                        gmxMMPBSA out files to parse. If set will be used over other variables.
  --hostfile FILENAME   text file with addresses of nodes of dask SSH cluster. The most typical, it can be passed as $PBS_NODEFILE variable from inside a PBS script. The first line in this file will be
                        the address of the scheduler running on the standard port 8786. If omitted, calculations will run on a single machine as usual.
  -c INTEGER, --ncpu INTEGER
                        number of CPU per server. Use all cpus by default.
  --ligand_id UNL
  --clean_previous      Clean previous temporary gmxMMPBSA files

```

### **Examples**
```
run_gbsa  --wdir_to_run md_files/md_run/protein_H_HIS_ligand_1 md_files/md_run/protein_H_HIS_ligand_2  -c 128 -m mmpbsa.in
```
**Output**   
*each run creates in the working directory (or in the current directory if wdir argument was not set up):*
 1) a unique streaMD log file  
 log_mmpbsa_*start-time*.log 
 Contains important information/warnings/errors about the main run_gbsa program run.
 2) a unique bash log file. 
 log_mmpbsa_bash_*start-time*.log   
 Contains stdout from gmx_MMPBSA 
 3) GBSA_output_*start*.csv with summary csv if MMGBSA method was run
 4) PBSA_output_*start*.csv with summary csv if MMPBSA method was run
 
 each wdir_to_run has FINAL_RESULTS_MMPBSA_*start-time*.csv with GBSA/PBSA output. 
 
### ProLIF Protein-Ligand Interaction Fingerprints
#### **USAGE**
```
$ run_prolif -h
usage: run_prolif [-h] [-i DIRNAME [DIRNAME ...]] [--xtc FILENAME] [--tpr FILENAME] [-l STRING] [-s INTEGER] [-a STRING] [-d WDIR] [-v] [--hostfile FILENAME] [-c INTEGER]

Get protein-ligand interactions from MD trajectories using ProLIF module.

optional arguments:
  -h, --help            show this help message and exit
  -i DIRNAME [DIRNAME ...], --wdir_to_run DIRNAME [DIRNAME ...]
                        single or multiple directories with simulations.
                                                     Should consist of: md_out.tpr and md_fit.xtc files (default: None)
  --xtc FILENAME        input trajectory file (XTC). Will be ignored if --wdir_to_run is used (default: None)
  --tpr FILENAME        input topology file (TPR). Will be ignored if --wdir_to_run is used (default: None)
  -l STRING, --ligand STRING
                        residue name of a ligand in the input trajectory. (default: UNL)
  -s INTEGER, --step INTEGER
                        step to take every n-th frame. ps (default: 1)
  -a STRING, --append_protein_selection STRING
                        the string which will be concatenated to the protein selection atoms. Example: "resname ZN or resname MG". (default: None)
  -d WDIR, --wdir WDIR  Working directory for program output. If not set the current directory will be used. (default: None)
  -v, --verbose         print progress. (default: False)
  --hostfile FILENAME   text file with addresses of nodes of dask SSH cluster. The most typical, it can be passed as $PBS_NODEFILE variable from inside a PBS script. The first line in this file will be the address of the scheduler running on the standard port 8786. If omitted, calculations will run on a single machine as usual. (default: None)
  -c INTEGER, --ncpu INTEGER
                        number of CPU per server. Use all cpus by default. (default: 64)


```

### **Examples**
```
run_prolif  --wdir_to_run md_files/md_run/protein_H_HIS_ligand_1 md_files/md_run/protein_H_HIS_ligand_2  -c 128 -v -s 5
```
**Output**  
1) in each directory where xtc file is located  *plifs.csv* file for each simulation will be created
2) *prolif_output.csv* - aggregated csv output file for all analyzed simulations
###Licence
BSD-3