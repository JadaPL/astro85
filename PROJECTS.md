# CS85 astronomy teaser projects

Thirty one-week projects, each with a starter script in `starters/` that downloads real data and makes a first plot. The number on each project matches its starter file.

**Key:** ★ = data maintained by Harvard/Smithsonian (Center for Astrophysics) · † = brand-new or largely unexplored data · "Free sign-up" = needs a free account; everything else works anonymously.

**The week:** plan Tuesday (your question, the data, your first plot, what you'll demo Thursday, your biggest risk), build Tuesday to Thursday, and give a 5-minute demo of your prototype Thursday.

## The changing sky: Rubin alerts, novae, variable stars

### 01. Rubin alert explorer †

- **Question:** What is a brand-new transient from the Rubin Observatory doing, night by night and filter by filter?
- **Data:** Rubin's public alert stream (live since Feb 2026) via the ALeRCE broker: light curves, classifications and image cutouts. Browse objects at https://lsst.alerce.online; Python client docs at https://alerce.readthedocs.io. Access: anonymous.
- **Starter:** [`starters/01_rubin_alerts.py`](starters/01_rubin_alerts.py)
- **First plot:** The object's multi-band light curve (flux vs. time, one color per Rubin filter).
- **Thursday prototype:** A notebook "alert explorer": paste any Rubin object ID and get its light curve, ALeRCE's class probabilities (client.query_probabilities) and its science/template/difference cutouts (client.plot_stamps, Jupyter only).
- **Stretch:** Pull 20 objects of one class and compare how fast they rise and fade. If the example ID returns nothing, pick a fresh one from the explorer site.

### 02. Nova watch: the "Blaze Star" T CrB

- **Question:** T Coronae Borealis erupts about every 80 years and is overdue (no eruption yet as of this fall). Is it showing warning signs, and how fast did this year's nova V1452 Tau fade?
- **Data:** AAVSO International Database: brightness measurements of variable stars from observers worldwide, going back over a century. Docs: https://docs.aavso.org/observations. Access: free sign-up for an AAVSO API key; step-by-step instructions are at the top of the starter.
- **Starter:** [`starters/02_nova_watch.py`](starters/02_nova_watch.py)
- **First plot:** T CrB's V-band brightness since January 2025 (or V1452 Tau's decline since August 2026).
- **Thursday prototype:** A "Nova Watch" dashboard: T CrB's recent light curve with an eruption alarm line, next to V1452 Tau's fade with measured t2/t3 (days to fade by 2 and 3 magnitudes).
- **Stretch:** Overlay T CrB's 1946 eruption from Harvard's plate archive (project 3). Note: T CrB is near the Sun in the sky in Nov-Dec, so recent data are sparse.

### 03. A century of a star ★ †

- **Question:** What did T CrB do over 100 years, including its 1946 explosion, as recorded on Harvard's own glass photographic plates?
- **Data:** DASCH DR7 (Digital Access to a Sky Century @ Harvard): brightness measurements from hundreds of thousands of digitized Harvard plates, about 1885-1992. https://dasch.cfa.harvard.edu/dr7/ via the daschlab package. Access: anonymous (an optional free account raises rate limits).
- **Starter:** [`starters/03_dasch_century.py`](starters/03_dasch_century.py)
- **First plot:** About a century of T CrB brightness, with "not seen" upper limits in gray and the 1946 eruption as a spike.
- **Thursday prototype:** A "century light curve" notebook: type any star name, get its DASCH light curve, and compare it with modern survey data.
- **Stretch:** Run it on Boyajian's star (KIC 8462852) and test the claim that it dimmed over the last century.

### 04. Variable star period finder

- **Question:** Can you measure a pulsating star's period from unevenly spaced ground-based data as precisely as the Kepler space telescope did?
- **Data:** Zwicky Transient Facility (ZTF) public light curves: about 6 years of photometry for over a billion objects. IRSA API docs: https://irsa.ipac.caltech.edu/docs/program_interface/ztf_lightcurve_api.html. Access: anonymous.
- **Starter:** [`starters/04_variable_period.py`](starters/04_variable_period.py)
- **First plot:** The RR Lyrae star V782 Cyg folded at its best Lomb-Scargle period, with Kepler's period in the title for comparison.
- **Thursday prototype:** A notebook or small app: enter coordinates, get the periodogram and folded light curve, plus a table comparing your periods with catalog values for 5 stars.
- **Stretch:** Show how the star's color changes through the pulsation, or use Gaia distances to test the RR Lyrae brightness-distance relation.

### 05. Satellites vs. astronomy

- **Question:** How fast is Starlink filling the sky that telescopes look through?
- **Data:** GCAT: Jonathan McDowell's (longtime CfA astrophysicist) catalog of every launched object since 1957, updated daily. https://planet4589.org/space/gcat/. Access: anonymous.
- **Starter:** [`starters/05_satellites.py`](starters/05_satellites.py)
- **First plot:** Satellites launched per year from 1957 to 2026, with Starlink stacked in red.
- **Thursday prototype:** A dashboard with launches per year, satellites still in orbit, and Starlink's share, plus a "tonight's sky" panel.
- **Stretch:** Count the Starlinks above Cambridge tonight with skyfield and CelesTrak's CSV data (https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=csv; download at most once every 2 hours). Use CSV, not TLE: new satellites now have 6-digit catalog numbers.

## Planetary defense and the solar system

### 06. Close-approach dashboard

- **Question:** How many asteroids will pass Earth in the next year, how many come closer than the Moon, and are the big ones always farther away?
- **Data:** JPL Close-Approach Data API: every known near-Earth-object approach, with miss distance and brightness. https://ssd-api.jpl.nasa.gov/doc/cad.html. Access: anonymous.
- **Starter:** [`starters/06_close_approach.py`](starters/06_close_approach.py)
- **First plot:** Every approach in the next 365 days: date vs. miss distance in Moon distances, sized and colored by estimated diameter.
- **Thursday prototype:** A small Streamlit app or notebook with sliders for the date window and distance cutoff, a "closest 10" table, and a size-vs-distance plot.
- **Stretch:** Query past approaches back to 1900 and show how many close passers were found each year as surveys improved.

### 07. Impact risk explorer

- **Question:** Which known asteroids could still hit Earth, and how did 2024 YR4 go from a ~3% chance of hitting Earth to a near miss of the Moon?
- **Data:** JPL CNEOS Sentry API: the official list of objects with possible future Earth impacts, plus objects that have been removed from it. https://ssd-api.jpl.nasa.gov/doc/sentry.html. Access: anonymous.
- **Starter:** [`starters/07_sentry_risk.py`](starters/07_sentry_risk.py)
- **First plot:** Every Sentry object: impact probability vs. Palermo scale, sized by diameter, top 5 labeled. The script also prints 2024 YR4's current status.
- **Thursday prototype:** A risk-explorer notebook with the Sentry table, a histogram of when objects get removed, and a 2024 YR4 timeline (Earth risk ruled out in 2025; JWST observations in Feb 2026 ruled out a 2032 Moon impact).
- **Stretch:** Use the removed-objects list (?removed=1) to show how quickly most "threats" disappear once more observations arrive.

### 08. Interstellar comet 3I/ATLAS and Apophis 2029 †

- **Question:** How does a visitor from another star move through our solar system compared with the planets, and how close will Apophis come to Earth on April 13, 2029?
- **Data:** JPL Horizons: NASA's position calculator for any planet, comet or asteroid, via astroquery. https://ssd-api.jpl.nasa.gov/doc/horizons.html. Access: anonymous.
- **Starter:** [`starters/08_interstellar_apophis.py`](starters/08_interstellar_apophis.py)
- **First plot:** Left: the paths of 3I/ATLAS, Earth and Mars around the Sun. Right: Apophis's distance from Earth around the 2029 flyby, compared with geostationary satellites.
- **Thursday prototype:** An animation (GIF) of the 3I/ATLAS flyby, plus a speed-vs-distance plot showing it moves faster than the Sun's escape speed.
- **Stretch:** Compare the three known interstellar objects ('Oumuamua, Borisov, 3I/ATLAS) on one plot.

### 09. Fireball map

- **Question:** Where on Earth do small asteroids explode in the atmosphere, and how often does a Chelyabinsk-size blast happen?
- **Data:** CNEOS Fireball API: bright fireballs detected by US government sensors since 1988, with location and energy. https://ssd-api.jpl.nasa.gov/doc/fireball.html. Access: anonymous.
- **Starter:** [`starters/09_fireball_map.py`](starters/09_fireball_map.py)
- **First plot:** A whole-Earth map of every located fireball, sized and colored by impact energy; the title names the largest event.
- **Thursday prototype:** An interactive map with a year slider (plotly), plus a plot of how many events per year exceed each energy.
- **Stretch:** Fit a power law and estimate how often a Tunguska-size (megaton) event should happen.

### 10. Every asteroid orbit, and Rubin's new discoveries ★ †

- **Question:** What does the asteroid belt look like when you plot all ~1.5 million known orbits, and where do near-Earth objects and this year's (Rubin-era) discoveries fall?
- **Data:** MPCORB from the Minor Planet Center (hosted at the Harvard-Smithsonian CfA): the master file of every known asteroid orbit. Format: https://docs.minorplanetcenter.net/mpc-ops-docs/orbits/minor-planet-orbit-format/. Access: anonymous (one-time download of roughly 100 MB).
- **Starter:** [`starters/10_mpc_orbits.py`](starters/10_mpc_orbits.py)
- **First plot:** Orbit size vs. eccentricity for every known asteroid, with near-Earth objects in red and 2026 designations in blue. Look for the Kirkwood gaps.
- **Thursday prototype:** A notebook with the orbit plot, a histogram with the Kirkwood gaps labeled at Jupiter resonances, and discoveries per half-month in 2024-2026 to show the Rubin-era jump.
- **Stretch:** For ~100 objects designated in 2026, fetch their observations from the MPC API and estimate what share Rubin (observatory code X05) discovered.

### 11. Organic molecules on Mars (advanced)

- **Question:** Can you see, in Curiosity's own raw chemistry data, the signals of organic molecules like benzene and chlorobenzene baked out of ancient Martian rock?
- **Data:** Curiosity rover SAM instrument (gas chromatograph-mass spectrometer) data in NASA's Planetary Data System. https://pds-geosciences.wustl.edu/missions/msl/sam.htm. Access: anonymous (one ~20 MB text file).
- **Starter:** [`starters/11_mars_sam_gcms.py`](starters/11_mars_sam_gcms.py)
- **First plot:** Counts vs. time for three molecular masses (benzene, toluene, chlorobenzene) during one oven-heating and gas-chromatograph run (sol 1546).
- **Thursday prototype:** A notebook that turns one experiment into a real chromatogram and compares its peaks with the SAM team's identified-molecule table for that experiment.
- **Stretch:** Compare two experiments from different rocks. Backup if the file format fights you: map NASA's Meteorite Landings dataset (data.nasa.gov).

## The Sun and space weather (including the National Solar Observatory)

### 12. Solar cycle forecaster

- **Question:** This solar cycle peaked well above the official 2019 forecast. How wrong were the experts, and when will the Sun go quiet again?
- **Data:** SILSO monthly sunspot numbers since 1749 (https://sidc.be/SILSO/) and NOAA Space Weather Prediction Center cycle forecasts (https://services.swpc.noaa.gov/json/solar-cycle/). Access: anonymous.
- **Starter:** [`starters/12_solar_cycle.py`](starters/12_solar_cycle.py)
- **First plot:** All 25 sunspot cycles since 1749, plus a zoom on the current cycle vs. the 2019 forecast and NOAA's latest forecast band.
- **Thursday prototype:** A notebook that measures every cycle's peak, timing and length, fits the current cycle, and predicts when the next minimum arrives.
- **Stretch:** Test whether how fast a cycle rises predicts how high it peaks (the Waldmeier effect), then forecast Cycle 26.

### 13. Solar flare statistics

- **Question:** For every X-class flare, how many smaller flares does the Sun produce? Does flare size follow a power law, like earthquakes?
- **Data:** GOES X-ray flare events in the Heliophysics Events Knowledgebase (https://www.lmsal.com/hek/), queried with sunpy. Access: anonymous.
- **Starter:** [`starters/13_flare_powerlaw.py`](starters/13_flare_powerlaw.py)
- **First plot:** Flare frequency vs. peak X-ray flux for every 2024 GOES flare, with a power-law fit.
- **Thursday prototype:** Repeat the fit for each year from 2011 to 2026 and plot the slope and flare rate against the sunspot cycle.
- **Stretch:** Use a proper maximum-likelihood power-law fit instead of a straight line on a log plot.

### 14. Can magnetic fields predict a big flare?

- **Question:** Do sunspot regions show measurable magnetic "stress" before they unleash X-class flares, enough for a simple classifier to beat guessing?
- **Data:** SDO/HMI SHARP active-region measurements from Stanford's JSOC (http://jsoc.stanford.edu) via the drms package; flare labels from project 13. Access: anonymous for the measurements used here (image downloads need a free JSOC email registration).
- **Starter:** [`starters/14_sharp_keywords.py`](starters/14_sharp_keywords.py)
- **First plot:** Hourly magnetic flux and current helicity of the region that produced the biggest flare of the last cycle (X9.3, Sept 2017), with the flare marked.
- **Thursday prototype:** Label each region-day "big flare in next 24 h: yes/no", train a simple scikit-learn classifier, and compare it with always guessing "no".
- **Stretch:** Show which magnetic features matter most, and test on a held-out year.

### 15. Watching solar filaments live and die (NSO GONG)

- **Question:** How do the dark plasma filaments above the Sun's surface grow, drift and sometimes suddenly erupt over a single day?
- **Data:** National Solar Observatory GONG network: full-disk hydrogen-alpha images of the Sun every minute since 2010. https://gong2.nso.edu/ftp/HA/ (info: https://nso.edu/data/nisp-data/h-alpha/). Access: anonymous. Please be gentle: NSO asks users not to bulk-download, so take at most ~100 images (e.g., one every 10 minutes).
- **Starter:** [`starters/15_gong_halpha.py`](starters/15_gong_halpha.py)
- **First plot:** A full-disk hydrogen-alpha image of the Sun showing dark filaments, bright active regions and prominences on the edge.
- **Thursday prototype:** A time-lapse GIF of 1-2 days and a simple "filament tracker" that measures the dark area over time.
- **Stretch:** Find a filament that vanishes between frames (an eruption) and check whether a flare or CME was reported then. If the URL fails, try removing "ftp/" from it.

### 16. What has the world's biggest solar telescope seen? (NSO DKIST) †

- **Question:** The 4-meter Inouye Solar Telescope just resolved ~20 km whirlpools on the Sun (Nature, Aug 2026). What has it observed since 2022, and how much is public yet?
- **Data:** NSO DKIST Data Center inventory (instrument, date, wavelength, embargo status, seeing quality) via the dkist package. https://dkist.data.nso.edu. Access: searching is anonymous; downloading image files needs a free Globus account plus Globus Connect Personal (stretch only).
- **Starter:** [`starters/16_dkist_inventory.py`](starters/16_dkist_inventory.py)
- **First plot:** Every DKIST dataset as observation date vs. wavelength, colored by instrument, plus a printed count of public vs. embargoed datasets.
- **Thursday prototype:** A dashboard of DKIST's holdings: filter by instrument and seeing quality, and show when embargoed data become public.
- **Stretch:** Get a free Globus account and download one small public image set, or watch the short public DKIST movies at https://dkist.virtualsolar.org (no sign-up).

### 17. Space weather dashboard: aurora tonight? †

- **Question:** When a gust of fast solar wind with a southward magnetic field hits Earth, how quickly do geomagnetic storms follow?
- **Data:** NOAA Space Weather Prediction Center real-time solar wind (now including NOAA's new SOLAR-1 spacecraft) and the planetary K-index. https://services.swpc.noaa.gov/json/rtsw/ and https://services.swpc.noaa.gov/products/. Access: anonymous.
- **Starter:** [`starters/17_space_weather.py`](starters/17_space_weather.py)
- **First plot:** Solar wind speed, density and magnetic field (Bz) for the last ~24 hours, plus 7 days of the K-index with storms in red.
- **Thursday prototype:** An auto-refreshing dashboard that saves every download so a full week of solar wind builds up, and flags "aurora watch" conditions.
- **Stretch:** Use your logged week to fit a simple model that predicts the K-index from wind speed and Bz.

## Black holes, gravitational waves and cosmic rays

### 18. The stellar graveyard (LIGO) †

- **Question:** How heavy are the black holes and neutron stars that collide across the universe, and are there masses nature seems to avoid?
- **Data:** LIGO-Virgo-KAGRA's Gravitational-Wave Transient Catalog (through GWTC-5.0, 2026, ~390 events) from the Gravitational Wave Open Science Center. https://gwosc.org. Access: anonymous.
- **Starter:** [`starters/18_stellar_graveyard.py`](starters/18_stellar_graveyard.py)
- **First plot:** Primary vs. secondary mass for every merger with published masses, colored by distance, with the neutron-star/black-hole dividing line.
- **Thursday prototype:** A notebook with mass histograms, how the catalog grew from 2015 to 2026, and final mass vs. distance.
- **Stretch:** Color by spin and look for mergers inside the predicted "pair-instability" mass gap (about 50-130 solar masses).

### 19. Hear a black hole merger (LIGO)

- **Question:** What did the first black-hole collision ever detected (2015) actually "sound" like in LIGO's detectors?
- **Data:** LIGO strain data for GW150914 from the Gravitational Wave Open Science Center (https://gwosc.org), downloaded with requests and read with gwpy. Access: anonymous (~1 MB).
- **Starter:** [`starters/19_hear_a_merger.py`](starters/19_hear_a_merger.py)
- **First plot:** A spectrogram showing the "chirp": the signal sweeping up in frequency in the last 0.2 seconds before merger. The script also writes a WAV file.
- **Thursday prototype:** An "audio gallery" with spectrograms, playable chirps and a short explainer of why the pitch rises, for 2-3 events.
- **Stretch:** Repeat for GW250114, the loudest event so far (larger download, ~100 MB).

### 20. Where do the highest-energy particles come from?

- **Question:** Do the most energetic particles ever recorded (like the Oh-My-God and Amaterasu particles) come from particular places in the sky, such as nearby active galaxies?
- **Data:** Pierre Auger Observatory catalog of its 100 highest-energy cosmic rays, 2004-2020 (https://opendata.auger.org/catalog/index.php). Access: anonymous.
- **Starter:** [`starters/20_cosmic_ray_skymap.py`](starters/20_cosmic_ray_skymap.py)
- **First plot:** A sky map in galactic coordinates of Auger's top events, sized by energy, with Centaurus A and the Amaterasu and Oh-My-God arrival directions marked.
- **Thursday prototype:** Count events near Centaurus A and compare with 1,000 shuffled skies to get a simple significance.
- **Stretch:** Use Auger's larger public data release (via TAP at https://dc.g-vo.org/tap, table auger3.ev_sd1500) to look for the large-scale dipole above 8 EeV.

### 21. Chandra X-ray source explorer ★ †

- **Question:** Which young stars in the Orion Nebula are blasting out X-rays, and do the faint ones have more energetic spectra?
- **Data:** Chandra Source Catalog 2.2 (released Oct 2026; ~430,000 X-ray sources) from the Chandra X-ray Center at the CfA. https://cxc.cfa.harvard.edu/csc/. Access: anonymous.
- **Starter:** [`starters/21_chandra_explorer.py`](starters/21_chandra_explorer.py)
- **First plot:** X-ray hardness vs. brightness for every catalogued source around the Orion Nebula Cluster.
- **Thursday prototype:** A small app: type any target name and get a sky plot, a hardness-brightness diagram and a table; compare Orion, the Andromeda galaxy and the Galactic Center.
- **Stretch:** Find flaring young stars using the catalog's variability columns, or cross-match with Gaia distances.

### 22. Hidden black holes in Gaia

- **Question:** Can we find black holes that emit no light at all just by watching the stars that orbit them wobble?
- **Data:** Gaia DR3 binary-star orbits (gaiadr3.nss_two_body_orbit) from the ESA Gaia Archive (https://gea.esac.esa.int/archive/). Access: anonymous.
- **Starter:** [`starters/22_gaia_dark_companions.py`](starters/22_gaia_dark_companions.py)
- **First plot:** Mass function vs. orbital period for tens of thousands of Gaia binaries, with candidates whose unseen companion must be heavier than 3 Suns highlighted in red.
- **Thursday prototype:** A notebook ranking the top 20 candidates, showing where the known Gaia black holes (BH1, BH2) fall, and explaining why most "candidates" are spurious.
- **Stretch:** Estimate each companion's minimum mass. (Gaia's next data release, DR4, arrives Dec 2, after this project, so it's a natural follow-up.)

### 23. Fast radio bursts †

- **Question:** Do fast radio bursts that repeat come from different distances or environments than ones we see only once?
- **Data:** Second CHIME/FRB Catalog (Jan 2026): 4,539 bursts from 3,641 sources. https://chime-frb.ca/catalogs/catalog2. Access: anonymous.
- **Starter:** [`starters/23_fast_radio_bursts.py`](starters/23_fast_radio_bursts.py)
- **First plot:** Dispersion measure (a proxy for distance) for one-off bursts vs. repeaters.
- **Thursday prototype:** A dashboard comparing repeaters and one-offs in distance, burst width and spectrum, with statistical tests and a sky map.
- **Stretch:** Turn dispersion measure into a rough redshift and flag the most distant bursts.

## Stars, planets and life

### 24. Our neighborhood in 3D

- **Question:** What does every star within 100 parsecs (~326 light-years) of the Sun look like, and where are the white dwarfs?
- **Data:** Gaia DR3 from the ESA Gaia Archive (https://gea.esac.esa.int/archive/): positions, distances and colors for 1.8 billion stars. Access: anonymous.
- **Starter:** [`starters/24_gaia_neighborhood.py`](starters/24_gaia_neighborhood.py)
- **First plot:** A Hertzsprung-Russell diagram (color vs. brightness) of nearby stars, showing the main sequence, giants and the white-dwarf sequence.
- **Thursday prototype:** An HR diagram linked to a 3D map of the same stars: select a region of the diagram and see where those stars are.
- **Stretch:** Go farther out and look for the Radcliffe Wave, a giant wave of star-forming gas discovered at the CfA in 2020.

### 25. Find a transiting planet

- **Question:** Can you discover a planet yourself just by watching a star dim for a few hours every few days?
- **Data:** TESS 2-minute light curves from NASA's MAST archive (https://mast.stsci.edu) via lightkurve. Access: anonymous.
- **Starter:** [`starters/25_transit.py`](starters/25_transit.py)
- **First plot:** Left: a period search with a sharp peak at 0.94 days. Right: the star's light folded on that period, showing a ~1%-deep transit.
- **Thursday prototype:** A "transit hunter" notebook: type a star name, get its period, folded transit and planet radius, and compare with the NASA Exoplanet Archive.
- **Stretch:** Recover the small planet Pi Mensae c, or run a blind search on an unconfirmed TESS planet candidate.

### 26. Exoplanet population explorer

- **Question:** Of the ~6,000 known planets, which sizes and orbits are common, and why are planets 1.5-2 times Earth's size rare (the "radius valley")?
- **Data:** NASA Exoplanet Archive, Planetary Systems Composite table. https://exoplanetarchive.ipac.caltech.edu (TAP docs: https://exoplanetarchive.ipac.caltech.edu/docs/TAP/usingTAP.html). Access: anonymous.
- **Starter:** [`starters/26_exoplanet_population.py`](starters/26_exoplanet_population.py)
- **First plot:** Planet radius vs. orbital period, colored by discovery method, with the radius valley shaded.
- **Thursday prototype:** A dashboard with filters (discovery year, method, star temperature) and a radius histogram where the valley shows up as a dip.
- **Stretch:** Keep only precisely measured planets and watch the valley sharpen; test whether it shifts with star type.

### 27. Molecules in a planet's air (JWST)

- **Question:** How can starlight passing through a planet's atmosphere tell us which molecules are there, and could we spot molecules made by life the same way?
- **Data:** JWST Early Release Science data for planet WASP-39 b, from the paper that first found carbon dioxide in an exoplanet atmosphere (Nature 2023). https://zenodo.org/records/6959427. Access: anonymous (375 kB).
- **Starter:** [`starters/27_jwst_molecules.py`](starters/27_jwst_molecules.py)
- **First plot:** WASP-39 b's transmission spectrum with the H2O, CH4, SO2, CO2 and CO bands marked; look for the big CO2 bump at 4.3 microns.
- **Thursday prototype:** A "molecule finder" that compares the different data reductions and measures how strongly each band is detected.
- **Stretch:** Compute molecular absorption from HITRAN, the line database maintained at the CfA (free sign-up for a HITRAN API key), and study the contested 2025 claim of a possible biosignature gas on K2-18 b.

## Galaxies and the universe

### 28. How far back can JWST see? †

- **Question:** How many galaxies do we now know from the universe's first 500 million years?
- **Data:** DAWN JWST Archive merged table: redshifts for 80,000+ public JWST spectra across the deep fields. https://zenodo.org/records/15472354 (project: https://dawn-cph.github.io/dja/). Access: anonymous (133 MB).
- **Starter:** [`starters/28_jwst_redshifts.py`](starters/28_jwst_redshifts.py)
- **First plot:** A histogram of JWST redshifts from 0 to 14, with a printed count of galaxies beyond redshift 10.
- **Thursday prototype:** A dashboard comparing deep fields, with a sky map of one field and a table of the most distant galaxies.
- **Stretch:** Add color image cutouts of the most distant galaxies from the archive's cutout service.

### 29. Quasar redshift finder (DESI)

- **Question:** How do astronomers measure the distance to a quasar 10+ billion light-years away from the pattern of its spectral lines?
- **Data:** DESI Data Release 1 (23 million spectra) through NOIRLab's SPARCL service. https://astrosparcl.datalab.noirlab.edu. Access: anonymous.
- **Starter:** [`starters/29_quasar_spectrum.py`](starters/29_quasar_spectrum.py)
- **First plot:** One DESI quasar spectrum at redshift ~2.4 with its model fit, and markers where its emission lines land after redshifting.
- **Thursday prototype:** A simple redshift finder that tries many redshifts, scores how well the lines match, and checks itself against DESI's answers for 50 quasars.
- **Stretch:** Extend it to ordinary galaxies, or study the "Lyman-alpha forest" of intergalactic hydrogen.

### 30. The Hubble diagram and dark energy

- **Question:** Distant exploding stars look fainter than they should in a universe of matter alone. Does that force us to accept dark energy?
- **Data:** Pantheon+ catalog of 1,701 Type Ia supernova measurements. https://github.com/PantheonPlusSH0ES/DataRelease. Access: anonymous (566 kB).
- **Starter:** [`starters/30_hubble_diagram.py`](starters/30_hubble_diagram.py)
- **First plot:** Distance vs. redshift for the supernovae, with models with and without dark energy, and the difference between them.
- **Thursday prototype:** A notebook with a dark-energy slider plus a simple fit that reports the best value and how strongly "no dark energy" is ruled out.
- **Stretch:** Fit the Hubble constant, or explore DESI's 2025 hint that dark energy changes over time.
