C  CONF_INT.F  CALCULATES THE INTERVAL OF CONFIDENCE FROM 
C  A SET OF THERMAL HISTORIES.
      implicit double precision (a-h,o-z)	
      parameter(ns=400,cn=12,R=1.987D-3,dt=20.d0,tau1=3.,tau2=1)
      parameter(tim=3.15576d13,pi=3.14159265,nt=1000)
      dimension temp(nt,ns),time(nt,ns),xtem(ns),nch(ns)
      dimension xmed(ns),ave(ns),adev(ns),sdev(ns),xmed2(ns),
     $  var(ns),skew(ns),curt(ns),xage(ns),xmed1(ns)
***  Comment out next line to compile with old Microsoft Developer Studio
c	character line*40
      external temfc
	open(unit=22,file='mchist-out.dat',status='old')
	open(unit=24,file='statanal.dat')
      open(unit=26,file='average.dat')
      open(unit=29,file='confmed.dat')
	open(unit=30,file='input.dat')
	  open(unit=51,file='confint.cl')
      ncyc = 0
      ncurv = 0
C	DEFINE AGE RANGE
C  MINIMUM AGE
C	print *,'Define Age range and mesh'
C	print *, 'Input Initial age'
	read(51,*) agein
C      write(30,*)'Initial age= ',agein
C  MAXIMUM AGE
C	print *, 'Input Final age'
	read(51,*) agend
C	write(30,*)'Final age= ',agend
C  NUMBER OF AGE INTERVALS
C	print *, 'Input number of age intervals'
	read(51,*) nsteps
C	write(30,*)'number of age intervals= ',nsteps
	dage = (agend - agein)/nsteps
C  READ THERMAL HISTORIES
	ks=1
	kend=0
1	n=1
2     read(22,*,END=20,ERR=30)time(n,ks),temp(n,ks)
      n=n+1
      goto 2
20	kend=-1
30    nch(ks)=n-1
      if (nch(ks).eq.0.and.kend.eq.0)goto 1
      if (nch(ks).eq.0.and.kend.eq.-1)goto 13
      ks=ks+1
      if(ks.gt.ns)stop 'too many thermal histories'
***  Comment out next line to compile with old Microsoft Developer Studio
c	read(22,120,END=20)line
      goto 1
13    ks=ks-1
C  CALCULATES THE XTEM VECTOR FOR EACH TIME     
	do 10 j=1,nsteps+1
	    xage(j) = agein + (j-1)*dage
            if(j.eq.nsteps+2)xage(j)=agend
	    xmed(j) = 0
	    do 22 k=1,ks
	    	if (xage(j).gt.time(1,k))goto 10
            xtem(k) = temfc(time(1,k),temp(1,k),nch(k),xage(j))
22	    continue
C	    STATISTICAL CALCULATIONS
C	    MEAN OF THE DISTRIBUTION	    
	    call moment(xtem,ks,ave(j),adev(j),sdev(j),
     $     var(j),skew(j),curt(j))
          call mdian1(xtem,ks,xmed(j))
          call binom(ks+1,j1,j2)
          nperc = ks*.05
          print *, nperc, ks
          if(nperc.eq.0)then
            write(29,*)'Not enough solutions to calculate 
     $       confidence intervals'
            stop 'ERROR: not enough solutions'
          endif
          if(j.eq.1)then
               xmed0=xtem(j2)
               xmed02=xtem(ks-nperc)
          endif
          xmed1(j)=xtem(j1)
          xmed2(j)=xtem(nperc)
C  WRITE INTERVAL OF CONFIDENCE, MEAN AND MEDIAN
          write(24,110)xage(j),ave(j),xmed(j),sdev(j),adev(j),
     $      var(j),skew(j),curt(j)
          write(26,110)xage(j),ave(j),xmed(j),xmed(j)+sdev(j),
     $      xmed(j)-sdev(j)
          write(29,110)xage(j),xtem(ks-nperc),xtem(j2)    
10	continue 
      do 12 j=nsteps+1,1,-1
          write(29,110)xage(j),xmed2(j),xmed1(j)   
12	continue 
          write(29,110)xage(1),xmed02,xmed0
100	format(100(I5,1x))
110   format(8f8.2)
120   format(A40)
	end

C FUNCTION TEMFC (CALCULATES THE TEMPERATURE AT ANY GIVEN AGE)
      double precision function temfc(time,temp,ni,x)
      implicit double precision (a-h,o-z)
      dimension time(ni),temp(ni)
      temfc = 0.d0
      if(x.eq.time(1))then
         temfc=temp(1)
         return
      endif
      do 10 j=ni-1,1,-1
        if(time(j).gt.x.and.time(j+1).le.x)then
          slope =  (temp(j+1)-temp(j))/(time(j+1)-time(j))
          temfc=temp(j)+ slope * (x-time(j))
          return
       endif
10    continue
      end
      
C  SUBROUTINE MDIAN1 
C  Given an array X of N numbers, returns their median value XMED. The
C  array X is modified and returned sorted into ascending order 
C  (Num. Recipes, p.460)      
      subroutine mdian1(x,n,xmed)
      implicit double precision (a-h,o-z)
      dimension x(n)
      call sort(n,x)
      n2=n/2
      if(2*n2.eq.n)then
        xmed=0.5*(x(n2)+x(n2+1))
      else
        xmed=x(n2+1)
      endif
      return
      end

C  SUBROUTINE SORT
C  Sorts an array RA of length N into ascending numerical order using
C  the Heapsort algorithm. N is input; RA is replaced on output by its
C  sorted rearrangement. (Num. Recipes p.231)     
      subroutine sort(n,ra)
      implicit double precision (a-h,o-z)
      dimension ra(n)
      l=n/2+1
      ir=n
10    continue
        if(l.gt.1)then
          l=l-1
          rra=ra(l)
        else
          rra=ra(ir)
          ra(ir)=ra(1)
          ir=ir-1
          if(ir.eq.1)then
            ra(1)=rra
            return
          endif
        endif
        i=l
        j=l+l
20      if(j.le.ir)then
          if(j.lt.ir)then
            if(ra(j).lt.ra(j+1))j=j+1
          endif
          if(rra.lt.ra(j))then
            ra(i)=ra(j)
            i=j
            j=j+j
          else
            j=ir+1
          endif
        go to 20
        endif
        ra(i)=rra
      go to 10
      end


C  SUBROUTINE MOMENT
C  Given an array of DATA of length N, this routine returns its mean AVE
C  average deviation ADEV, standard deviation SDEV,  variance VAR, skewness
C  SKEW, and kurtosis CURT. (Num. Recipes. p.458)
      subroutine moment(data,n,ave,adev,sdev,var,skew,curt)
      implicit double precision (a-h,o-z)
      dimension data(n)
      if(n.le.1)pause 'n must be at least 2'
      s=0.
      do 11 j=1,n
        s=s+data(j)
11    continue
      ave=s/n
      adev=0.
      var=0.
      skew=0.
      curt=0.
      do 12 j=1,n
        s=data(j)-ave
        adev=adev+abs(s)
        p=s*s
        var=var+p
        p=p*s
        skew=skew+p
        p=p*s
        curt=curt+p
12    continue
      adev=adev/n
      var=var/(n-1)
      sdev=sqrt(var)
      if(var.ne.0.)then
        skew=skew/(n*sdev**3)
        curt=curt/(n*var**2)-3.  
      else
        print *, 'zero variance: no skew or kurtosis'
        skew = 0.
        curt = 0.
      endif
      return
      end


C	BINOM.F	
C ***********************************************************************
       subroutine binom(n,j1,j2)
      implicit double precision (a-h,o-z)
      if(n/2*2-n.eq.0)then
        nmed=n/2
      else
        nmed=(n+1)/2
      endif
C  SEARCH FOR F(M)=0.5
      do 10 j=nmed,1,-1
	 faux=f
         f=0.
         j1=j
         do 12 k=1,j
            f = bico(n,k)*0.5d0**n + f
12       continue
         if(f.le.0.05)then
            if(dabs(faux-.05).lt.dabs(f-.05))j1=j1+1
	    goto 14
          endif
10    continue
14    do 20 j=nmed+1,n
         faux = f
         f=0.
         j2=j
         do 22 k=1,j
            f = bico(n,k)*0.5d0**n + f
22       continue         
         if(f.ge.0.95)then
            if(dabs(faux-.95).lt.dabs(f-.95))j2=j2-1
	    return
         endif
20    continue
      stop 'error on binom sub'
      end

      double precision function bico(n,k)
      implicit double precision (a-h,o-z)
      bico=dnint(dexp(factln(n)-factln(k)-factln(n-k)))
      return
      end

      double precision function factln(n)
      implicit double precision (a-h,o-z)
      dimension a(100)
      data a/100*-1.d0/
      if (n.lt.0) pause 'negative factorial'
      y=1.d0+n
      if (n.le.99) then
        if (a(n+1).lt.0.) a(n+1)=gammln(y)
        factln=a(n+1)
      else
        factln=gammln(y)
      endif
      return
      end

      function gammln(xx)
      implicit double precision (a-h,o-z)
      real*8 cof(6),stp,half,one,fpf,x,tmp,ser
      data cof,stp/76.18009173d0,-86.50532033d0,24.01409822d0,
     *    -1.231739516d0,.120858003d-2,-.536382d-5,2.50662827465d0/
      data half,one,fpf/0.5d0,1.0d0,5.5d0/
      x=xx-one
      tmp=x+fpf
      tmp=(x+half)*dlog(tmp)-tmp
      ser=one
      do 11 j=1,6
        x=x+one
        ser=ser+cof(j)/x
11    continue
      gammln=tmp+dlog(stp*ser)
      return
      end
