---
layout: post
title: Optimization
author: Jake Ross
comments: True
categories: 
- blog 
---

<!--========================== Blog =========================-->
Speeding up the analysis loading process would greatly enhance usablity and the UX. 

Many attempts have been made to optimize this process with varying degrees of success.
A new branch feature/new_db was created to explore database optimizations that could speed up db queries. Initial
testing with a db of ~35k analyses show ~40% increase in speed. These numbers should be verified. The new db migration
is tricky so effort should be put into optimization without radical database changes. 

From initial testing it appears the major bottle neck occurs when construction the Isotope objects for each
analysis; ~50 ms per analysis. It is currently unclear how isotope construction time can be minimized. 
Traits overhead maybe considerable but it doesn't seem likely the Traits dependency can be removed. 

### Low hangin fruit

- temporally cache irradiation data. When loading multiple analyses use a irradiation cache. Maintaining
 the cache outside of a session may be necessary as sqlachemy does internal caching. This suggests that 
 little to no performance gain will be achieved by discarding the irradiation cache at the end of ``make_analyses``.
- optimize the sync process. optimize DBAnalysis.sync. investigate all aspects of the sync process except isotope
 construction
 
write a benchmarking module for systematic analysis of the changes and their effect. 

<!--=========================== EOF =========================-->