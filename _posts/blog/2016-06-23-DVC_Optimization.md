---
layout: post
title: Improved Analyses loading
author: Jake Ross
comments: True
categories: 
- blog 
- Sample
- Sample Prep
---

<!--========================== Blog =========================-->

I finally succeeded in speeding up loading analyses from the database. In reality retrieval from the database 
is quite rapid (depending on network connection) but converting to ```DVCIsotopeRecordViews``` was time consuming. One 
earlier optimization was to limit the number of ```progress.change_message``` calls. ```change_message``` eventually 
calls ```Qt.QApplication.process_events``` which takes ~80ms each call. So loading of analyses was already penalized 
80ms because of the progress bar. I will continue to investigate the progress window but a more significant speed up 
was achieved by eliminating the concept of an ```IsotopeRecordView```. (eventually this model should be extended to the 
other record view classes). 

So... the major change was to keep the session open when a ```SessionCTX``` is exited and to temporarily disable 
```expire_on_commit``` when retrieving analyses. Since the analyses do not change in the database it is safe to 
disable ```expire_on_commit``` 

<!--=========================== EOF =========================-->