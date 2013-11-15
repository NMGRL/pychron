         IMPLICIT DOUBLE PRECISION (A-H,O-Z)
      parameter(ns=200,r=1.987E-3,pi=3.141592654)
	DIMENSION sig(ns)
	DIMENSION T(0:ns),DTIM(0:ns),age(0:ns)
	dimension terrage(0:ns),clage(0:ns),errclage(0:ns)
	common /var/ f(0:ns),telab(ns),tilab(ns),xlogd(0:ns),sig39(ns),  
     $xlogr(0:ns),a39(ns),acut,b,sige,sigo,qmax,chisqe 

	CHARACTER*9  TAB1,sname*50,yes*3
	TAB1=CHAR(09)

  5	print *,'Want to read samples from list (yes)?'
 	read *,yes
	if(yes(1:1).eq.'y')then
	  print *,'Enter filename that contains the list of samples'
	  read(*,'(a50)')sname
	  kn=name(sname) 
	  open(unit=50,file=sname(1:kn),status='old',ERR=5)
	endif
1	if(yes(1:1).eq.'y')then
       read(50,'(a50)',END=501)sname
	 print *,sname
	else
	 print *,'Enter sample name (stop to exit)'
	 read(*,'(a50)')sname
	 if(sname(1:4).eq.'stop')stop
	endif
	kn=name(sname) 
	open(unit=17,file=sname(1:kn)//'.in',status='old')
	open(unit=16,file='arr.smp')
	open(unit=19,file='log.smp')
	open(unit=11,file='temstep.in')
	open(unit=21,file='age-sd.smp')
	open(unit=22,file='age-cl.smp')
	open(unit=23,file='fj.in')
      open(unit=24,file='sig.in')
      open(unit=25,file='age.in')
      open(unit=26,file=sname(1:kn)//'_a39.in')
      open(unit=30,file=sname(1:kn)//'_ener.dat')

  120	format(1x,I3)

30	n = n+1
	read(17,*,END=35)nstp,t(n),dtim(n),a39(n),sig39(n),f(n),age(n)
     $	,sig(n),terrage(n),clage(n),errclage(n)
	t(n)= t(n) + 273.
	f(n) = f(n)/100.d0
	age(n) = age(n)
	sig(n) = sig(n)
	telab(n)=t(n)

   	goto 30
35	write(11,120)n-1
      if(f(n-1).eq.1.0)f(n-1)=0.999999
	do 20 j=1,n-1
          write(23,*)f(j)
	    write(11,*)t(j)
	    write(11,*)dtim(j)
   	dtim(j)=60.*dtim(j)
   20	tilab(j)=dtim(j)


	do 80 k=1,n-1
	   write (21,*)f(k-1)*100.,age(k)+sig(k)
	   write (21,*)f(k)*100.,age(k)+sig(k)
	   write (22,*)f(k-1)*100.,clage(k)+errclage(k)
	   write (22,*)f(k)*100.,clage(k)+errclage(k)
         write (25,*)f(k)*100.,clage(k)
         write (24,*)errclage(k)
         write (26,*)a39(k),sig39(k)
   80	continue

	nt = n-1
	do 90 k=1,n-1
	write (21,*)f(nt-k+1)*100.,age(nt-k+1)-sig(nt-k+1)
	write (21,*)f(nt-k)*100.,age(nt-k+1)-sig(nt-k+1)
	write (22,*)f(nt-k+1)*100.,clage(nt-k+1)-errclage(nt-k+1)
	write (22,*)f(nt-k)*100.,clage(nt-k+1)-errclage(nt-k+1)
   90	continue
	write (21,*)f(1)*100.,age(2)+sig(2)
 	write (22,*)f(1)*100.,clage(2)+errclage(2)

      call arr(nt,yes) 
  100	format(1x,'&')
	 n=0
	close(17)
	close(16)
	close(19)	
	close(11)
	close(21)
	close(22)
	close(23)
	close(24)	
	close(25)
	close(30)
	goto 1
  501	stop
	END

      function name(sname)  
      character sname*50  
      do 10 j=1,50  
        if(sname(j:j).eq.' ')then  
          if(j.eq.1)stop 'name starts with empty space'  
          name = j-1  
          return  
        endif  
        name = 50  
10    continue  
      return  
      end  

c	t(n) = temperature (C)
c  	a2 = 40Ar/39Ar
c	a37(j) = 37Ar/39Ar
c	a4 = 36Ar/39Ar
c	a5 = mol 39Ar
c	f39(n) = fraction of 39Ar
c	a6 = % 40Ar*
c	a7 = 40Ar*/39Ark
c	age(n)= Apparent age in yr
c	sig(n)= sigma uncertainty of age in yr
c	time(n) = time in minutes
c	a8 = 39Ar/40Ar
c	a9 = sigma uncertainty 39Ar/40Ar
c	a10= 36Ar/40Ar
c	a11= sigma uncertainty of 36Ar/40Ar
c	Tinv= Inverse of temperature
c	a13= sigma  uncertainty of Temperature
c	xlog= log(D/r**2)
c	a15= sigma uncertainty of log(D/r**2)
C	SUBROUTINE ARR.F
C **********************************************************************
	subroutine arr(nt,yes)  
      implicit double precision (a-h,o-z)  
      parameter(nca=20,ns=200,r=1.987E-3,pi=3.141592654)
      parameter(ee=0.4342944879,ngauss=10)  
      dimension wt(ns)  
      common /var/ f(0:ns),telab(ns),tilab(ns),xlogd(0:ns),sig39(ns),  
     $xlogr(0:ns),a39(ns),acut,b,sige,sigo,qmax,chisqe  
      common /int/ ni,imp,nimax,ke  
      character  tab1*9, yes*1
      tab1=char(09)  
      ni=nt    
      nloop = 1 
      f(0) = 0.  
      b=8.  
      imp=2.  
      acut = 0.5  
      dchmin = 0.01  
      ncons = 0.  
      nimax = ni  
      do 10 nt=1,ni  
        if(ni.eq.nimax.and.telab(nt).gt.1373)nimax = nt-1  
10    continue  
      call diff(ord,E,wt,xro,yes)  
c      call weight(wf)  
      write(*,101) 'E=',e,' +- ',sige,'     Ordinate=',ord,' +-',sigo 
	write(30,*)	
	write(30,101)'E=',e,' +- ',sige,'     Ordinate=',ord,' +-',sigo 

	close(30)
   
      return
  100 format(G20.8) 
  101 format(1x,A3,f8.4,A5,f8.4,A14,f8.4,A5,f8.4)
  102 format(A50)  
  105 format(f12.8)  
  110 format(1X,5(F12.8,A1))  
  115 format(1X,I4,3x,f9.5,7x,f9.5)  
  116 format(1x,A10,A1,8(f8.5,1x),i2)  
  120 format(I7)  
  130 format(6x,'tinv',8x,'Log(D/r2)',7x,'f(k)*100',8x,  
     $'Log(r/ro)',8x,'39Ar-av')  
  140 format(1x,'domain #',10x,'volume fraction',15x,'domain size')  
  150 format(1x,'&')  
  160 format(A7)  
  170 format(1x,i4,4(a1,g20.8))  
  180 format(a10,4(a1,f7.4),a1,i2,2(g14.8),2i6)  
      end  
  

C       SUBROUTINE DIFF.F
C	SUBROUTINE PARAM.F  
C  	SUBROUTINES FIT, GSER, and GCF  - FUNCTIONS GAMMQ and GAMMLN  
  
      subroutine diff(ord,E,wt,xro,yes)  
      implicit double precision (a-h,o-z)  
      parameter(ns=200,r=1.987E-3,pi=3.141592654,ee=0.4342944879)  
      dimension tinv(ns),wt(ns)  
      common /var/ f(0:ns),telab(ns),tilab(ns),xlogd(0:ns),sig39(ns),  
     $xlogr(0:ns),a39(ns),acut,b,sige,sigo,qmax,chisqe  
      common /int/ ni,imp,nimax,ke  
      character tab1*9, yes*1  
      tab1=char(09)  
      xlogr(0)=0.  
C     CALCULATION OF LOG(D/R^2)  
      do 10 k=1,ni  
        if (f(k).le.acut) then  
          xlogr(k)=pi*(f(k)/4.)**2  
        else  
          xlogr(k)=-dlog(pi**2/b*(1.-f(k)))/pi**2  
        endif  
10    continue  
      sumwt = 0.  
      nix = ni  
      call errcal(wt,sumwt)  
      do 20 k=1,ni  
         if(nix.eq.ni.and.telab(k).gt.1373)nix=k-1  
         xlogd(k) = dlog10((xlogr(k)-xlogr(k-1))/tilab(k)*imp**2)  
         tinv(k)=1./telab(k)*10000.  
         write(16,110)tinv(k),tab1,xlogd(k),tab1,wt(k)  
20    continue  
   
      call param(tinv,wt,e,ord,yes)  
      slop = e*ee/(r*10000)  
      xro = (ord-slop*tinv(nix)-xlogd(nix))/2.*(1.+ (1.-f(nix))/2.)  
      do 30 k=1,ni  
        xlogr(k)=(ord-slop*tinv(k)-xlogd(k))/2.  
        write(19,110)f(k-1)*100.,tab1,xlogr(k)  
        write(19,110)f(k)*100.,tab1,xlogr(k)  
30    continue  
      return  
110   format(1X,5(F12.8,A1)) 
100	format(1x,i5,5(f16.8))	 
      end  
  
C     SUBROUTINE PARAM.F  
      subroutine param(tinv,wt,e,ord,yes)  
      implicit double precision (a-h,o-z)  
      parameter(ns=200,r=1.987E-3,pi=3.141592654,ee=0.4342944879  
     $,nstop=20,mwt=1,dtp=5.d0)  
      dimension tinv(ns),wt(ns),y(ns),alog(ns),x1(ns),y1(0:ns),wty(ns)  
     $,wtx(ns)  
	dimension tinvaux(nstop+5),xlogdaux(nstop+5),wtaux(nstop+5),
     $telabaux(nstop+5),prm(nstop)
      common /var/ f(0:ns),telab(ns),tilab(ns),xlogd(0:ns),sig39(ns),  
     $xlogr(0:ns),a39(ns),acut,b,sige,sigo,qmax,chisqe  
      common /int/ ni,imp,nimax,ke  
      character tab1*9,yes*1,yesp*1  
      tab1=char(09)  
      nst = nstop  
      y(3)=0.  
      if(ni.lt.nstop) then  
         nst = ni  
      endif
	  
      ki=0  
	if(yes.ne.'y')then
      Print *,'Do you want to exclude some points' 
      Print *, 'from E calculation (yes/no)?'
	read *,yesp
	 if (yesp.eq.'y')then
	   print *, 'How many points do you want to remove?'
	   read *, np
	   do 4 k=1,np
	     Print *, 'Enter the step # of the point(s) to be removed'
	     read *, prm(k)
4        continue
         k0=1
         k1=1
	   k2=1
5	 continue
	  if (prm(k0).eq.k1)then
	   k1=k1+1
	   k0=k0+1
	   if(k1.le.nst)goto 5
	 endif
	   tinvaux(k2)=tinv(k1)
	   xlogdaux(k2)=xlogd(k1)
	   wtaux(k2)=wt(k1)
	   telabaux(k2)=telab(k1)
	   k2=k2+1
	   k1=k1+1
	   if(k1.le.nst)goto 5
	   nst=k2-1
	   goto 6
	 endif
	endif

15    qmaxk = 0.  
      qmax=1.  
      sx1=0.  
	   do 3 k=1,nst
	      tinvaux(k)=tinv(k)
	      xlogdaux(k)=xlogd(k)
	      wtaux(k)=wt(k)
	      telabaux(k)=telab(k)
3        continue
	

6      do 12 j=1,3  
           x1(j)=tinvaux(ki+j)  
           sx1 = sx1 + x1(j)  
           y1(j)=xlogdaux(ki+j)  
           wty(j)=wtaux(ki+j)  
           wtx(j)=10000.d0*dtp/telabaux(ki+j)**2  
12    continue  
      do 10 k=4,nst  
        x1(k)=tinvaux(ki+k)  
        sx1 = sx1 + x1(k)  
        y1(k)=xlogdaux(ki+k)  
        wty(k)=wtaux(ki+k)  
        wtx(k)=10000.d0*dtp/telabaux(ki+k)**2  
        if(x1(k).eq.sx1/k)goto 10  
        ncont=1  
	do 16 j=2,k  
           ks = 0  
           do 14 j1=1,j-1  
               if(x1(j).eq.x1(j1))ks=1  
14	   continue  
           if(ks.eq.0)ncont=ncont+1  
16      continue  
        call fit(x1,y1,k,wtx,wty,a,bf,siga,sigb,chi2,q)  
        if(q/qmax.lt.1.e-10)goto 24  
        y(k) = -r*bf*10000./ee  
        alog(k) = a 
        sige1 = r*sigb*10000./ee  
        qs=k*q  
 	  write(30,100)k,y(k),sige1,alog(k),siga,qs
        if(qs.gt.qmaxk.and.ncont.ge.3)then  
          ke=k  
          if(qs.gt.qmaxk)qmaxk=qs  
          qmax=q  
          chisqe=chi2  
          sige = sigb*r*10000.d0/ee  
          sigo = siga  
          e=y(k)  
          ord=alog(k)  
        endif  
10    continue  
24    continue  
      if(ki.eq.0.and.qmax.lt.0.05)then  
        ki=1  
        goto 15  
      endif  
100   format(1x,i5,5(f14.6),2g20.8)  
110   format(1X,5(F12.8,A1))  
      return  
      end  
  
      subroutine fit(x,y,ndata,sigx,sigy,a,b,siga,sigb,chi2,q)  
      implicit double precision (a-h,o-z)  
      parameter(nd=20,imax=20,xerr=1.d-3)  
      dimension x(ndata),y(0:ndata),sigx(ndata),sigy(ndata),wt(nd)  
      r=0.  
      b=-1.  
      iter = 0  
1     sx=0.  
      sy=0.  
      st2=0.  
      st3=0.  
      ss=0.  
      b0=b        
      do 11 i=1,ndata  
        wt(i)=1./(sigy(i)**2 + b**2*sigx(i)**2 - 2.d0*r*sigx(i)*sigy(i))  
        ss=ss+wt(i)  
        sx=sx+x(i)*wt(i)  
        sy=sy+y(i)*wt(i)  
11    continue  
      sxoss=sx/ss  
      syoss=sy/ss  
      do 13 i=1,ndata  
         t1=(x(i)-sxoss)*sigy(i)**2  
         t2=(y(i)-syoss)*sigx(i)**2*b  
	 t3= sigx(i)*sigy(i)*r  
         st2=st2+wt(i)**2*(y(i)-syoss)*(t1+t2-t3*(y(i)-syoss))  
         st3=st3+wt(i)**2*(x(i)-sxoss)*(t1+t2-b*t3*(x(i)-sxoss))            
13    continue  
      b=st2/st3  
      iter = iter + 1  
      if(iter.gt.imax)stop 'FIT2: TOO MANY ITERATIONS'  
      if(dabs(b0-b).gt.xerr)goto 1  
      a=(syoss-sxoss*b)  
       sgt1 = 0.  
       sgt2 = 0.  
      do 14 i=1,ndata  
          sgt1= sgt1 + wt(i)*(x(i)-sxoss)**2  
          sgt2= sgt2 + wt(i)*x(i)**2  
14    continue  
      sigb=dsqrt(1./sgt1)  
      siga=sigb*dsqrt(sgt2/ss)  
      chi2=0.  
        do 16 i=1,ndata  
          chi2=chi2+wt(i)*(y(i)-a-b*x(i))**2  
16      continue  
        q=gammq(0.5d0*(ndata-2),0.5d0*chi2)  
      return  
      end  
  
  
      subroutine weight(wf)  
      implicit double precision (a-h,o-z)  
      parameter(ns=200)  
      dimension wf(ns)  
      common /var/ f(0:ns),telab(ns),tilab(ns),xlogd(0:ns),sig39(ns),  
     $xlogr(0:ns),a39(ns),acut,b,sige,sigo,qmax,chisqe  
      common /int/ ni,imp,nimax,ke  
      sumwt = 0  
	do 20 k=1,ni  
	   wf(k)=1./dsqrt(f(k)-f(k-1))  
	   sumwt = sumwt + wf(k)  
20	continue	  
	do 25 k=1,ni  
	    wf(k) = wf(k)/sumwt  
25	continue  
	return  
	end  

      subroutine errcal(wt,swt)  
      implicit double precision (a-h,o-z)  
      parameter(ns=200,r=1.987E-3,pi=3.141592654,ee=0.4342944819,  
     $sigt0=90.d0,a0=-0.19354d0,a1=-0.62946d0,  
     $a2=0.13505d0,a3=-0.01528d0)  
      dimension sigzit(0:ns),wt(ns),sigf(0:ns),siga(0:ns) 
      dimension sigsm(ns),f1(0:ns)  
      common /var/ f(0:ns),telab(ns),tilab(ns),xlogd(0:ns),sig39(ns),  
     $xlogr(0:ns),a39(ns),acut,b,sige,sigo,qmax,chisqe  
      common /int/ ni,imp,nimax,ke  
C CALCULATION OF SIGMA F  
C TO GENERALIZE TO HAVE POINTS WITH DIFFERENT % ERRORS  
C READ SIGA FROM SOME FILE.  
        
      sumat = 0  
	do 14 n=1,ni
14    sumat = sumat + a39(n)  
  
       f1(0)=0.d0  
      do 16 j=1,ni  
        sigsm(j)=sig39(j)/sumat 
	  siga(j)=sig39(j)/a39(j) 
16    continue  
      an1 = pi**2  
      sigat = 0.  
      swt = 0.  
      sigzit(0)=0.  
      do 10 i=1,ni  
c         x=dlog10(sig39(i))+15.d0  
c        siga0=a0+a1*x+a2*x**2+a3*x**3  
c        siga0 = 10**(siga0-2.d0)  
c	   siga0 =0.
         sigat = sigat + sigsm(i)**2  
         sigf(i)=sigat   
10    continue  
C       sigat = sigat + 0.000  
C  CALCULATION OF SIGMA DELTA XI  
      do 30 i=1,ni  
         if (f(i).le.acut) then  
            fp = f(i)+f(i-1)  
            as1 = 1.d0/fp**2-2.d0/fp  
            as2 = (f(i)**2-2*f(i)*(f(i)**2-f(i-1)**2))/fp**2  
            sigzit(i) = 4.d0*(sigat + sigf(i-1)*as1+siga(i)**2*as2)  
         else  
            dzit2 = (dlog((1-f(i))/(1-f(i-1)))/an1)**2  
c            as1= (sigsm(i)/(an1*(1-f(i-1))))**2/dzit2  
             as1 = ((f(i)-f(i-1))/an1)**2/(1-f(i-1))**2
	       sigzit(i)= ((sigat-sigf(i))/(1-f(i))**2 + siga(i)**2)*as1
		   sigzit(i)=sigzit(i)/dzit2
         endif  
30    continue  
CALCULATION OF SIGMA LOG  
      do 40 i=1,ni         
         sigt = (sigt0/tilab(i))**2  
         wt(i) = dsqrt(sigt+sigzit(i))*ee  
         swt = swt + wt(i)  
         rate = dsqrt(sigzit(i)/sigt)  
40     continue  
100    format(1x,6(f12.8))  
       return  
       end  
  

      double precision function gammq(a,x)  
      implicit double precision (a-h,o-z)  
      if(x.lt.0..or.a.le.0.)stop 'ERROR(GAMMQ): (x.lt.0..or.a.le.0.)'  
      if(x.lt.a+1.)then  
        call gser(gamser,a,x,gln)  
        gammq=1.-gamser  
      else  
        call gcf(gammcf,a,x,gln)  
        gammq=gammcf  
      endif  
      return  
      end  
  
      subroutine gser(gamser,a,x,gln)  
      implicit double precision (a-h,o-z)  
      parameter (itmax=100,eps=3.e-7)  
      gln=gammln(a)  
      if(x.le.0.)then  
        if(x.lt.0.)stop 'ERROR(GSER): (x.lt.0.)'  
        gamser=0.  
        return  
      endif  
      ap=a  
      sum=1./a  
      del=sum  
      do 11 n=1,itmax  
        ap=ap+1.  
        del=del*x/ap  
        sum=sum+del  
        if(abs(del).lt.abs(sum)*eps)go to 1  
11    continue  
      stop 'ERROR(GSER): a too large, itmax too small'  
1     gamser=sum*dexp(-x+a*dlog(x)-gln)  
      return  
      end  
  
      subroutine gcf(gammcf,a,x,gln)  
      implicit double precision (a-h,o-z)  
      parameter (itmax=100,eps=3.e-7)  
      gln=gammln(a)  
      gold=0.  
      a0=1.  
      a1=x  
      b0=0.  
      b1=1.  
      fac=1.  
      do 11 n=1,itmax  
        an=float(n)  
        ana=an-a  
        a0=(a1+a0*ana)*fac  
        b0=(b1+b0*ana)*fac  
        anf=an*fac  
        a1=x*a0+anf*a1  
        b1=x*b0+anf*b1  
        if(a1.ne.0.)then  
          fac=1./a1  
          g=b1*fac  
          if(abs((g-gold)/g).lt.eps)goto 1  
          gold=g  
        endif  
11    continue  
      stop 'ERROR(GCF): a too large, itmax too small'  
1     gammcf=dexp(-x+a*dlog(x)-gln)*g  
      return  
      end  
  
      double precision function gammln(xx)  
	implicit double precision (a-h,o-z)  
      real*8 cof(6),stp,half,one,fpf,x,tmp,ser,xx  
      data cof,stp/76.18009173d0,-86.50532033d0,24.01409822d0,  
     * -1.231739516d0,.120858003d-2,-.536382d-5,2.50662827465d0/  
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

C*********************************************************************
