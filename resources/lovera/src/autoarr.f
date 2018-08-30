C	MAIN.F
C **********************************************************************

C	"PARAMETERS"

C	R= GAS CONSTANT KCAL/(MOL-K)
C	D0= FREQUENCY FACTOR (1/SEC) 

C	"INPUT"

C	NUSA=# OF SAMPLES 
C	NSAMP=# OF DIFFERENT DIFF. DOMAINs
C       E= ACTIVATION ENERGY (KCAL/MOL)
C	ORD = LOG (Doi/Ro**2)
C       C(J)= VOL. FRAC. OF Jth DOMAIN
C	RP(J)= PLATEAU SIZE (LOG(R/Ro) PLOT)
C	NI=# OF HEATING STEPS
C	TELAB = TEMP. STEP (K)
C	TILAB= STEP HEATING DURATION (MIN)

C	"OUTPUT"

C	TINV = INVERSE LAB. TEMP. (10000/K)
C	DZX = - LOG(D/R**2) (1/SEC)
C	F(J)*100 = CUMULATIVE % 39-AR RELEASED 
C	AVT = (F(J)+F(J-1))*50
C	XLOGR= LOG(R/Ro)
C	RAD(J) = SIZE OF THE Jth DIFF. DOMAIN
C       C(J) = VOL. FRAC. OF Jth DOMAIN


C	"INPUT FILES"		"UNIT"		"PROGRAM"
C	  TEMSTEP.IN		  10		  MAIN
C	  FJ.IN		  	      12		  MAIN

C	"OUTPUT FILES"		"UNIT"		"PROGRAM"
C	  ARR-ME.IN		  14		  MAIN
C	  PARAM.OUT		  28		  MAIN
C	  DIST.DAT		  32		  MAIN
C	  ARR.SAMP		  20		  DIFF
C	  LOGR.SAMP		  22		  DIFF
C	  ENER.OUT		  30		  PARAM
C	  ARR.DAT		  16		  ARR
C	  LOGR.DAT		  18		  ARR


C ***********************************************************************

      implicit double precision (a-h,o-z)
	parameter(nca=20,ns=200)
	dimension a1(nca),a2(nca),auxal(nca,nca),auxa2(nca)
	dimension telab(ns),tilab(ns),auxa1(nca),dyda(nca)
	dimension zi(0:ns),wf(ns),xlogd(0:ns),xlogr(0:ns)
	dimension covar(nca,nca),alpha(nca,nca),lista(nca),da(nca)
	dimension f39(0:ns),f(0:ns),wksp(nca),iwksp(nca)
	character  tab1*9, yes*1
	tab1=char(09)
	open(unit=10,file='temstep.in',status='old')
	open(unit=12,file='fj.in',status='old')
	open(unit=14,file='arr-me.in',status='unknown')
	open(unit=28,file='param.out',status='unknown')
	open(unit=32,file='dist.dat',status='unknown')

	pi=3.141592654
	ee=dexp(1.d00)
	R=1.987E-3
	f(0) = 0.
	zi(0)=0.
	b=8.
	imp=2.
	acut=.60
	dchmin = 0.01
	ncons = 0.
	ndom = 8
	mdom = 3

	open(unit=42, file='autoarr.cl', status='old')
	read (42,*) yes

C	print *,'This program calculates all the parameters
C     $ (i.e. E, Do, etc) necessary to model the 39Ar data.'
C     	print *, 'However, If you want to introduce your own parameters
C     $ enter "y" now, otherwise type "n" and relax.'

	read (42,*) yes

	If(yes.eq.'y') then  
C		print *, 'if you still want to use the default
C     $ value of an specific parameter, type 0 at the prompt'
C		print *
c		print *, ' type number of max domains, <= 10, (Default is 8)'
		read *, naux
		if(naux.ne.0)ndom=naux
		print *, ' type number of min domains, > 2  (Default is 3)'
		read *, naux
		if(naux.ne.0)mdom=naux
		print *,'to keep Do fix type 1, otherwise type 0'
		read *, ncons
	endif

	read(10,*)ni
	nimax = ni
	do 10 nt=1,ni
	  read(10,*)telab(nt),tilab(nt)
	  read(12,*)f39(nt)
		if(f39(nt).gt.0.2.and.nt.eq.1)then
		  read(12,*)f39(nt)
		  read(12,*)f39(nt)
		endif
	  tilab(nt)=60.*tilab(nt)
	  if(ni.eq.nimax.and.telab(nt).gt.1373)nimax = nt-1
10	continue

	call diff(ord,E,f39,telab,tilab,xlogr,xlogd,wf,ni,xro,yes)

	print *,'E=',e,'     Ordinate=',ord
	write(28,*)'E=',e,'     Ordinate=',ord
	write(28,*)
 	ni = nimax

	call zita(ni,zi,e,ord,tilab,telab)

	ckchisq=1.0e30
	ckchin = 1.0e30
	mct = 0
	iseed = xro
70	call guess(ndom,a1,a2,xro,iseed)
	if(mct.gt.30) then
         print *, 'Warning: Two many iterations, 
     $   Consult your computer vodoo'
	   if(ncicle.gt.0)ncicle=4
	   amax=0.
	   mct=0
	   chisq=1.0e30
	   goto 54
      endif
	nc = 0
	na = 2.*ndom -1
	do 12 j=1,na
	   lista(j)=j
12	continue
	mfit = na
	if(ncons.eq.1)mfit = na-1
	alamda = -1.
	kc=0.
	ch = -1.
	alam = 0.001

26    call mrqmin(zi,f39,wf,ni,a2,na,lista,mfit,covar,alpha,
     $   nca,chisq,alamda,amax)

	do 52 j=1,na,2
	    if(a2(j+1).lt.-14) amax=-1.
	do 52 k=1,na,2
	    if(j.eq.k) goto 52
	    if(a2(j).eq.a2(k)) amax=-1
52	continue
	if(amax.eq.-1.) then
	  mct = mct + 1
	  goto 70
	endif
	if(alam.gt.alamda)then
        nc = 0
	else
	  nc = nc + 1
	  if (nc.le.50) goto 38
	  mct = mct + 1
	  goto 70
	endif
	chisqn = chisq
	if(chisq.gt.1.) chisqn = 1.
	dchisq = abs((chisq - ch)/chisqn)
	kc = kc + 1
	if(dchisq.ge.dchmin.and.kc.le.100.or.kc.lt.5) goto 38
84	write(28, *)'# dom=',ndom,'    Isteps=',kc,
     $  '     nc=',nc,'   chisq=',chisq
	goto 54
72	alamda = 0.
	ndom = (na+1)/2

	call mrqmin(zi,f39,wf,ni,a2,na,lista,mfit,covar,
     $   alpha,nca,chisq,alamda,amax)
                
      if (amax.eq.-1)stop 'stop 1: Consult your vodoo'
	do 24 nt=1,ni
	   call funcs(zi(nt),a2,y,dyda,na,a1,amax)
	   f(nt) = y
	   if(amax.eq.-1)stop 'stop 3: Consult your vodoo'
   24	continue
	call sort3(2*ndom,a1,a2,da,wksp,iwksp)
	rpmax = a1(na)
	xlog = ord - 2.* dlog10(rpmax)
	write(14,120)ndom
	write(28,140)
	sumc = 0.
	do 28 j=1,na+1,2
	  write(14,100)e
	  ordj=xlog - 2.*dlog10(a1(j)/rpmax)
	  write(14,100)ordj
	  write(14,105)a1(j+1)
	  write(28,115)(j+1)/2,a1(j+1),a1(j)/rpmax
	  write(32,*)sumc,log(a1(j))
	  sumc = sumc + a1(j+1)
	  write(32,*)sumc,log(a1(j))
28	continue
	write(28,*)
	write(28,*)ckchisq
	slop = e*dlog10(ee)/10000./r
	write(14,*)slop
	write(14,*)ord
	call arr(f,tilab,telab,ni,e,ord)

	stop 'end iteration'

54	continue
	if(ckchisq.gt.chisq) then
		do 64 j=1,na+1
		   auxa2(j)=a2(j)
		do 64 k=1,na+1
		   auxal(j,k)=alpha(j,k)
64		continue
		auxna = na
		ckchisq= chisq
	endif
	if(ckchin.gt.chisq) then
		call funcs(zi(1),a2,y,dyda,na,auxa1,amax)
		if(amax.eq.-1)stop 'stop 2: Consult your vodoo'
	    ckchin = chisq
	endif
	if(ncicle.lt.4)then
	   ncicle = ncicle + 1
	else
	  call sort3(2*ndom,auxa1,a2,da,wksp,iwksp)
	  ndom = ndom -1
	  mct = 0
	  ncicle = 0
	  ckchin = 1.0e30
	  sumc = 0.
	  do 68 j=1,na,2
		write(32,100)sumc,log(auxa1(j))
		sumc = sumc + auxa1(j+1)
		write(32,*)sumc,log(auxa1(j))
68	  continue
	  write(32,150)
	  if(ndom.eq.mdom-1)then
	     do 66 j=1,auxna+1
	          a2(j)=auxa2(j)
	     do 66 k=1,auxna+1
	          alpha(j,k)=auxal(j,k)
66	     continue
	     na = auxna
	     mfit = na
	     if(ncons.eq.1)mfit=na-1
	     print *,'# of domains =',(na +1)/2
           amax = 0. 
	     goto 72
	   endif
	endif
	goto 70
38	ch = chisq
	alam = alamda
   	goto 26

  100	format(G20.8)
  105	format(f12.8)
  110	format(1X,5(F12.8,A1))
  115	format(1X,I4,3x,f9.5,7x,f9.5)
  120	format(I5)
  130	format(6x,"tinv",8x,"Log(D/r2)",7x,"f(k)*100",8x,
     $  "Log(r/ro)",8x,"39Ar-av")
  140	format(1x,'domain #',10x,'volume fraction',15x,'domain size')
  150	format(1x,'&')
  160	format(A7)
  170	format(1x,i4,4(a1,g20.8))
	end

C	SUBROUTINE ARR.F
C **********************************************************************

C	"PARAMETERS"

C	R= GAS CONSTANT KCAL/(MOL-K)
C	D0= FREQUENCY FACTOR (1/SEC) 

C	"INPUT"

C	NUSA=# OF SAMPLES 
C	NSAMP=# OF DIFFERENT DIFF. DOMAINs
C       E= ACTIVATION ENERGY (KCAL/MOL)
C	ORD = LOG (Doi/Ro**2)
C       C(J)= VOL. FRAC. OF Jth DOMAIN
C	RP(J)= PLATEAU SIZE (LOG(R/Ro) PLOT)
C	NI=# OF HEATING STEPS
C	TELAB = TEMP. STEP (K)
C	TILAB= STEP HEATING DURATION (MIN)

C	"OUTPUT"

C	TINV = INVERSE LAB. TEMP. (10000/K)
C	DZX = - LOG(D/R**2) (1/SEC)
C	F(J)*100 = CUMULATIVE % 39-AR RELEASED 
C	AVT = (F(J)+F(J-1))*50
C	XLOGR= LOG(R/Ro)
C	RAD(J) = SIZE OF THE Jth DIFF. DOMAIN
C       C(J) = VOL. FRAC. OF Jth DOMAIN


C ***********************************************************************
	subroutine arr(f,tilab,telab,ni,e,ord)
      implicit double precision (a-h,o-z)
      parameter(ns=200)
	dimension avt(ns)
	dimension telab(ni),f(0:ni),zx(ns),tilab(ni)
	character  tab1*9, mo*3
	tab1=char(09)
	open(unit=16,file='arr.dat',status='unknown')
	open(unit=18,file='logr.dat',status='unknown')

	pi=3.14159265
	ee=dexp(1.d00)
	R=1.987E-3
	b=8.
	imp=2
	acut=0.50
	mo = 'sla'

C	INVERSION OF 39-F

	do 20 k=1,ni
	if (f(k).gt.acut) goto 22
	if (mo.eq.'sph') goto 30
	zx(k+1)=pi*(f(k)/4.)**2
	goto 20	
   30	zx(k+1)=(2.-pi/3.*f(k)-2.*dsqrt(1.-pi/3.*f(k)))/pi
	goto 20
   22	zx(k+1)=-dlog(pi**2/b*(1.-f(k)))/pi**2
   20	continue
	zx(1)=0.
	slop=E*dlog10(ee)/10000./R
	do 26 k=1,ni
	avt(k)=(f(k)+f(k-1))/2.*100.
	dzx = dlog10((zx(k+1)-zx(k))/tilab(k)*imp**2)
	tinv=1./telab(k)*10000.
	xlogr=(ord-slop*tinv-dzx)/2.
	write(18,110)f(k-1)*100.,tab1,xlogr
	write(18,110)f(k)*100.,tab1,xlogr
   26	write(16,110)tinv,tab1,dzx
	write(16,*)'&'
	write(18,*)'&'
    2	continue

  110	format(1X,5(F12.8,A1))
	return
	end

C	SUBROUTINE DIFF.F
C	SUBROUTINE PARAM.F
C  	SUBROUTINES FIT, GSER, and GCF  - FUNCTIONS GAMMQ and GAMMLN


	subroutine diff(ord,E,f,telab,tilab,xlogr,xlogd,wt,ni,xro,yes)
      implicit double precision (a-h,o-z)
      parameter(ns=200)
	dimension f(0:ni),telab(ni),tilab(ni),xlogr(0:ni)
	dimension xlogd(0:ni),tinv(ns),wt(ni)
	character tab1*9, yes*1
      tab1=char(09)
	open(unit=20,file='arr.samp',status='unknown')
	open(unit=22,file='logr.samp',status='unknown')

	acut = 0.5
	imp = 2.
	b = 8.
	xlogr(0)=0.
	pi=3.141592654
	ee = dlog10(dexp(1.d00))
	r = 1.987e-3

C	CALCULATION OF LOG(D/R^2)

	do 10 k=1,ni
	   if (f(k).le.acut) then
	       xlogr(k)=pi*(f(k)/4.)**2
	   else
   	       xlogr(k)=-dlog(pi**2/b*(1.-f(k)))/pi**2
	   endif
10	continue

	sumwt = 0.
	nix = ni
	do 20 k=1,ni
	   if(nix.eq.ni.and.telab(k).gt.1423)nix=k-1
	   wt(k)=1./dsqrt(f(k)-f(k-1))
	   xlogd(k) = dlog10((xlogr(k)-xlogr(k-1))/tilab(k)*imp**2)
	   tinv(k)=1./telab(k)*10000.
   	   write(20,110)tinv(k),tab1,xlogd(k)
	   sumwt = sumwt + wt(k)
20	continue
	
	do 25 k=1,ni
	    wt(k) = wt(k)/sumwt
25	continue

C	CALCULATION OF E AND Do/Ro^2

	call param(ni,tinv,xlogd,wt,e,ord)

	if(yes.eq.'y')then
	    print *, 'Type activation energy in kcal/mol, E='
	    read *,auxe
		if(auxe.ne.0) then
		    e=auxe
		    print *, 'Enter ordenate of log.vs.10000/t plot, 
     *	  log(Do/ro^2)='
		    read *,ord
		endif
	endif
	slop = e*ee/(r*10000)
	xro = (ord-slop*tinv(nix)-xlogd(nix))/2.*(1.+ (1.-f(nix))/2.)
	if(yes.eq.'y')then
		print *, 'type the max plateau of log(r/ro)'
	    read *,auxro
		if(auxro.ne.0)xro = auxro
	endif
	print *,'all the parameters are set now, relax'

	do 30 k=1,ni
	   xlogr(k)=(ord-slop*tinv(k)-xlogd(k))/2.
	   write(22,110)f(k-1)*100.,tab1,xlogr(k)
	   write(22,110)f(k)*100.,tab1,xlogr(k)
30	continue
	return
110	format(1X,5(F12.8,A1))
	end


C	SUBROUTINE PARAM.F

	subroutine param(ni,tinv,xlogd,wt,e,ord)
      implicit double precision (a-h,o-z)
	parameter (ns=200, nstop =20, mwt = 1)
	dimension tinv(ni),xlogd(0:ni),wt(ni),y(ns),alog(ns)
      open(unit=30,file='ener.out',status='unknown')

	nst = nstop
	kmax = 2
	dymin = 100.
	ee = dlog10(dexp(1.d00))
	r = 1.987e-3
	y(2)=0.

	if(ni.lt.nstop) then
	   nst = ni
	endif

	do 10 k=3,nst
	  call fit(tinv,xlogd,k,wt,mwt,a,b,siga,sigb,chi2,q)
	  y(k) = -r*b*10000./ee
	  alog(k) = a
	  write(30,100)k,y(k),alog(k)
10	continue
	do 20 k=3,nst
	  dy = y(k+1)-y(k)
	  ddy = y(k-1)-2.*y(k)+y(k+1)
	  if(y(k).gt.y(kmax))kmax=k
	  if(abs(dy).le.dymin.and.ddy.le.0.)then
	     dymin = abs(dy)
		 kmin = k
	  endif
	  if(dy.lt.0.) then
	     ndec = ndec + 1
	  else
	     ndec = 0.
	  endif
	  if(ndec.gt.4) then
	     e = (y(kmin) + y(kmin+1))/2.
		 ord = (alog(kmin) + alog(kmin+1))/2
		 kmax=0
		 return
	  endif
20	continue
      if(kmax.gt.0)then
        e = y(kmax)
        ord = alog(kmax)
        print *, 'Warning: auto didnt get a real maximum for E.'
        print *, 'You should check the ener.out output file'
        print *, 'and calculate E manually if necessary.'
      endif

100	format(1x,i5,5(f16.8))	
	return
	end

C  SUBROUTINES FIT, GSER, and GCF  - FUNCTIONS GAMMQ and GAMMLN
      subroutine fit(x,y,ndata,sig,mwt,a,b,siga,sigb,chi2,q)
      implicit double precision (a-h,o-z)
      dimension x(ndata),y(0:ndata),sig(ndata)
      sx=0.
      sy=0.
      st2=0.
      b=0.
      if(mwt.ne.0) then
        ss=0.
        do 11 i=1,ndata
          wt=1./(sig(i)**2)
          ss=ss+wt
          sx=sx+x(i)*wt
          sy=sy+y(i)*wt
11      continue
      else
        do 12 i=1,ndata
          sx=sx+x(i)
          sy=sy+y(i)
12      continue
        ss=float(ndata)
      endif
      sxoss=sx/ss
      if(mwt.ne.0) then
        do 13 i=1,ndata
          t=(x(i)-sxoss)/sig(i)
          st2=st2+t*t
          b=b+t*y(i)/sig(i)
13      continue
      else
        do 14 i=1,ndata
          t=x(i)-sxoss
          st2=st2+t*t
          b=b+t*y(i)
14      continue
      endif
      b=b/st2
      a=(sy-sx*b)/ss
      siga=dsqrt((1.+sx*sx/(ss*st2))/ss)
      sigb=dsqrt(1./st2)
      chi2=0.
      if(mwt.eq.0) then
        do 15 i=1,ndata
          chi2=chi2+(y(i)-a-b*x(i))**2
15      continue
        q=1.
        sigdat=dsqrt(chi2/(ndata-2))
        siga=siga*sigdat
        sigb=sigb*sigdat
      else
        do 16 i=1,ndata
          chi2=chi2+((y(i)-a-b*x(i))/sig(i))**2
16      continue
c        q=gammq(0.5*(ndata-2),0.5*chi2)
      endif
      return
      end

      function gammq(a,x)
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
          if(abs((g-gold)/g).lt.eps)go to 1
          gold=g
        endif
11    continue
      stop 'ERROR(GCF): a too large, itmax too small'
1     gammcf=dexp(-x+a*dlog(x)-gln)*g
      return
      end

      double precision function gammln(xx)
      real*8 cof(6),stp,half,one,fpf,x,xx,tmp,ser
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

C   SUBROUTINE FUNCS
	Subroutine funcs(x,b,y,dyda,na,a,amax)
      implicit double precision (a-h,o-z)
	parameter (nmax=21)
	dimension a(na+1),dyda(na+1),b(na+1),csh(nmax)

c    the multiplication by 4 stands for the divition of Do

	if(na.eq.0)return
	pi = 3.141592654
	y= 0. 
	as = 1.
	do 5 j=1,na,2
	  if(b(j).lt.-50.)then
		a(j)=0
	  else
	  	a(j) = dexp(b(j))
	  endif
	  if(b(j+1).lt.-20.)then
	  	a(j+1)=0.
		csh(j+1)=0.
	  else
	  	a(j+1) = (1. + dtanh(b(j+1)))/2.
	        csh(j+1) = 0.5/dcosh(b(j+1))**2
	  endif
	  as=as - a(j+1)
   5	continue
	a(na+1) =as + a(na+1)
	if(a(na+1).le.0.)then
	  amax = -1.
	  return
      endif
	b(na+1) = dlog(a(na+1))
	do 10 i=1,na,2
	   arg = x/a(i)*4.
	   if (arg.le.0.2827) then  
	     gf = 2. * dsqrt(arg/pi)
	   else
	     if ((pi/2)**2*arg.gt.80) then
		   gf = 1.
	     else
		   gf = 1. - 8./pi**2 * dexp(-(pi/2)**2*arg)
	     endif
	   endif
         dgf = 0 
	   do 20 j=1,50000,2
	      arg1 = (j*pi/2.)**2*arg
	      if (arg1.gt.25.) goto 21
   	      dgf = dgf + 2. *  dexp(-arg1)
20       continue
   21    y = y + a(i+1) * gf 
	   dyda(i+1)= gf  * csh(i+1)
	   dyda(i) = -a(i+1) * dgf * arg
	   a(i)=dsqrt(a(i))
   10	continue
	return
	end

C	SUBROUTINE GUESS.F

	subroutine guess(ndom,a1,a2,xro,iseed)
      implicit double precision (a-h,o-z)
	dimension a1(2*ndom),a2(2*ndom)

C	SUBROUTINE TO GUESS C(J),R(J)
	na=2*ndom
	sum = 0.
	do 8 j=1,na,2
 	   a1(j+1)= 1. + 10. * ran(iseed)
	   sum = sum + a1(j+1)
8	continue
	do 9 j=1,na,2
 	   a1(j+1)= a1(j+1)/sum
9	continue
	sum =0 
	do 10 j=1,na-2,2
	    sum= 1 + 10. * ran(iseed) + sum
	    a1(na-2-j) = sum
10	continue
	do 11 j=1,na-2,2
	    a1(j) = a1(j)/sum * xro
11	continue	
	sum = a1(na)+a1(na-2)
	do 12 j=3,na-3,2
	 	a1(j) = a1(j) - dlog10(sum)
		sum = sum + a1(na-(j+1))
12	continue

C	'ro' IS THE INVERSE OF Ro (1/Ro)	
	ro = 10.**(a1(1))
	do 15 j=3,na-3,2
    	  a2(j)=a1(1)-a1(na-j)
15	continue
	do 17 j=3,na-3,2
	  a1(j)=a2(j)
17	continue
	a1(na-1)=dlog10(a1(na))
	do 20 j=1,na-3,2
	  a1(j)=a1(j+1)/(10.**a1(j)-10.**a1(j+2))
20	continue
	a1(na-1)=1.
	nloop = 0
29	continue
	ncont = 0
	nloop = nloop + 1
	do 35 j=1,na-3,2
	  rom = 0.
	  if (a1(j).gt.1.) stop 'a1(j) > 1.'
	  if(a1(j+2).lt.a1(j))then
		 ncont = 0
		 do 27 k=j,j+2,2
	        rom = rom + a1(k+1)/a1(k)
27		 continue
		 a1(j+2) = a1(j)
		 a1(j) = a1(j+1)/(rom - a1(j+3)/a1(j+2))
	   else
	     ncont = ncont + 1
	   endif
35	continue
	if (nloop.gt.30) stop 'nloop greater than 30 on guess' 
	if (ncont.lt.(ndom-1)) goto 29
	sumro = 0.
	do 30 j=1,na-1,2
	   sumro = sumro + a1(j+1)/a1(j)
30	continue

C	CALCULATION OF A2

	do 25 j=1,na-1,2
	   a2(j)=2.*dlog(a1(j)*ro)
	   z = 2. * a1(j+1) - 1.
	   a2(j+1) = 0.5 * dlog((z+1)/abs(z-1)) 
25	continue
	return
	end

      Double precision function ran(iseed)
      parameter(ia=7141,ic=54773,im=259200)
      iseed=mod(iseed*ia+ic,im)
      ran=float(iseed)/float(im)
      return
      end

C	SUBROUTINE INDEXX

      subroutine indexx(n,arrin,indx)
	implicit double precision (a-h,o-z)
      dimension arrin(n),indx(n)
      do 11 j=1,n,2
        indx(j)=j
11    continue
      l=n/4*2+ 1
      ir=n-1
10    continue
      if(l.gt.1)then
        l=l-2
        indxt=indx(l)
        q=arrin(indxt)
      else
        indxt=indx(ir)
        q=arrin(indxt)
        indx(ir)=indx(1)
        ir=ir-2
        if(ir.eq.1)then
          indx(1)=indxt
          return
        endif
      endif
      i=l
      j=l+l+1
20    if(j.le.ir)then
        if(j.lt.ir)then
          if(arrin(indx(j)).lt.arrin(indx(j+2)))j=j+2
        endif
        if(q.lt.arrin(indx(j)))then
          indx(i)=indx(j)
          i=j
          j=j+j+1
        else
          j=ir+2
        endif
        go to 20
      endif
      indx(i)=indxt
      go to 10
      end

C	SUBROUTINES MRQMIN, MRQCOF, GAUSSJ, COVSRT


      subroutine mrqmin(x,y,sig,ndata,a,ma,lista,mfit,
     *    covar,alpha,nca,chisq,alamda,amax)
	implicit double precision (a-h,o-z)
      parameter (mmax=20)
      dimension x(0:ndata),y(0:ndata),sig(ndata),a(ma+1),lista(ma),
     *  covar(nca,nca),alpha(nca,nca),atry(mmax),beta(mmax),da(mmax)
	save beta,atry,da,ochisq
      if(alamda.lt.0.)then
	  amax = 0.
	  do 25 j=1,ma,2
	    if(a(j)*3..gt.amax)amax=a(j)*3.
25	  continue
        kk=mfit+1
        do 12 j=1,ma
          ihit=0
          do 11 k=1,mfit
            if(lista(k).eq.j)ihit=ihit+1
11        continue
          if (ihit.eq.0) then
            lista(kk)=j
            kk=kk+1
          else if (ihit.gt.1) then
            stop 'ERROR(MRQMIN): improper permutation in lista'
          endif
12      continue
        if (kk.ne.(ma+1))stop 'ERROR(MRQMIN): improper perm. in lista'
        alamda=0.001
        call mrqcof(x,y,sig,ndata,a,ma,lista,mfit,alpha,beta,nca,chisq
     *       ,amax)
	  if(amax.eq.-1)return
        ochisq=chisq
        do 13 j=1,ma
          atry(j)=a(j)
13      continue
      endif
      do 15 j=1,mfit
        do 14 k=1,mfit
          covar(j,k)=alpha(j,k)
14      continue
        covar(j,j)=alpha(j,j)*(1.+alamda)
        da(j)=beta(j)
15    continue
      call gaussj(covar,mfit,nca,da,1,1,amax)
	if(amax.eq.-1.)return
      if(alamda.eq.0.)then
        call covsrt(covar,nca,ma,lista,mfit)
        return
      endif
21	sum = 0.
      do 16 j=1,mfit
        atry(lista(j))=a(lista(j))+da(j)
16    continue
	if(ma.ne.mfit) then
	  do 22 k=1,mfit-1,2
	     if(atry(k).ge.atry(ma).or.dabs(atry(k)).gt.amax) then
	        da(k)=da(k)/2.
	        goto 21
	     endif
22	  continue
	else
	  do 26 j=1,mfit,2
	     if(dabs(atry(j)).gt.amax)then
	       da(j)=da(j)/2.
	       goto 21
	     endif
26	  continue
	endif
      do 19 k=1,mfit-1,2
	sum = sum + (1. + dtanh(atry(k+1)))/2.
19    continue
      if (sum.ge.1.)then
	  do 20 k=1,mfit,2
	    da(k+1)=da(k+1)/2.
20	  continue
	  goto 21
      endif
	
      call mrqcof(x,y,sig,ndata,atry,ma,lista,mfit,covar,da,nca,chisq
     *,amax)
	if(amax.eq.-1)return
      if(chisq.lt.ochisq)then
        alamda=0.1*alamda
        ochisq=chisq
        do 18 j=1,mfit
          do 17 k=1,mfit
            alpha(j,k)=covar(j,k)
17        continue
          beta(j)=da(j)
          a(lista(j))=atry(lista(j))
18      continue
      else
        alamda=10.*alamda
        chisq=ochisq
      endif
      return
      end

      subroutine mrqcof(x,y,sig,ndata,a,ma,lista,mfit,alpha,beta,nalp,
     *chisq,amax)
	implicit double precision (a-h,o-z)
      parameter (mmax=20)
      dimension x(0:ndata),y(0:ndata),sig(ndata),alpha(nalp,nalp),
     *    beta(ma),dyda(mmax),lista(mfit),a(ma+1),a1(mmax)
      do 12 j=1,mfit
        do 11 k=1,j
          alpha(j,k)=0.
11      continue
        beta(j)=0.
12    continue
      chisq=0.
      do 15 i=1,ndata
        call funcs(x(i),a,ymod,dyda,ma,a1,amax)
	if(amax.eq.-1) then
	   chisq=1000000.
	   return
	endif
        sig2i=1./(sig(i)*sig(i))
        dy=y(i)-ymod
        do 14 j=1,mfit
          wt=dyda(lista(j))*sig2i
          do 13 k=1,j
            alpha(j,k)=alpha(j,k)+wt*dyda(lista(k))
13        continue
          beta(j)=beta(j)+dy*wt
14      continue
        chisq=chisq+dy*dy*sig2i
15    continue
      do 17 j=2,mfit
        do 16 k=1,j-1
          alpha(k,j)=alpha(j,k)
16      continue
17    continue
      return
      end

      subroutine gaussj(a,n,np,b,m,mp,amax)
	implicit double precision (a-h,o-z)
      parameter (nmax=50)
      dimension a(np,np),b(np,mp),ipiv(nmax),indxr(nmax),indxc(nmax)
      do 11 j=1,n
        ipiv(j)=0
11    continue
      do 22 i=1,n
        big=0.
        do 13 j=1,n
          if(ipiv(j).ne.1)then
            do 12 k=1,n
              if (ipiv(k).eq.0) then
                if (abs(a(j,k)).ge.big)then
                  big=abs(a(j,k))
                  irow=j
                  icol=k
                endif
              else if (ipiv(k).gt.1) then
                amax = -1.
	        return
              endif
12          continue
          endif
13      continue
        ipiv(icol)=ipiv(icol)+1
        if (irow.ne.icol) then
          do 14 l=1,n
            dum=a(irow,l)
            a(irow,l)=a(icol,l)
            a(icol,l)=dum
14        continue
          do 15 l=1,m
            dum=b(irow,l)
            b(irow,l)=b(icol,l)
            b(icol,l)=dum
15        continue
        endif
        indxr(i)=irow
        indxc(i)=icol
        if (a(icol,icol).eq.0.) then
	    amax = -1.
	    return
	endif
        pivinv=1./a(icol,icol)
        a(icol,icol)=1.
        do 16 l=1,n
          a(icol,l)=a(icol,l)*pivinv
16      continue
        do 17 l=1,m
          b(icol,l)=b(icol,l)*pivinv
17      continue
        do 21 ll=1,n
          if(ll.ne.icol)then
            dum=a(ll,icol)
            a(ll,icol)=0.
            do 18 l=1,n
              a(ll,l)=a(ll,l)-a(icol,l)*dum
18          continue
            do 19 l=1,m
              b(ll,l)=b(ll,l)-b(icol,l)*dum
19          continue
          endif
21      continue
22    continue
      do 24 l=n,1,-1
        if(indxr(l).ne.indxc(l))then
          do 23 k=1,n
            dum=a(k,indxr(l))
            a(k,indxr(l))=a(k,indxc(l))
            a(k,indxc(l))=dum
23        continue
        endif
24    continue
      return
      end

      subroutine covsrt(covar,ncvm,ma,lista,mfit)
	implicit double precision (a-h,o-z)
      dimension covar(ncvm,ncvm),lista(mfit)
      do 12 j=1,ma-1
        do 11 i=j+1,ma
          covar(i,j)=0.
11      continue
12    continue
      do 14 i=1,mfit-1
        do 13 j=i+1,mfit
          if(lista(j).gt.lista(i)) then
            covar(lista(j),lista(i))=covar(i,j)
          else
            covar(lista(i),lista(j))=covar(i,j)
          endif
13      continue
14    continue
      swap=covar(1,1)
      do 15 j=1,ma
        covar(1,j)=covar(j,j)
        covar(j,j)=0.
15    continue
      covar(lista(1),lista(1))=swap
      do 16 j=2,mfit
        covar(lista(j),lista(j))=covar(1,j)
16    continue
      do 18 j=2,ma
        do 17 i=1,j-1
          covar(i,j)=covar(j,i)
17      continue
18    continue
      return
      end

C	SUBROUTINE SORT3

      subroutine sort3(n,ra,rb,rc,wksp,iwksp)
	implicit double precision (a-h,o-z)
      dimension ra(n),rb(n),rc(n),wksp(n),iwksp(n)
      call indexx(n,ra,iwksp)
      do 11 j=1,n
        wksp(j)=ra(j)
11    continue
      do 12 j=1,n,2
        ra(j)=wksp(iwksp(j))
	  ra(j+1)=wksp(iwksp(j)+1)
12    continue
      do 13 j=1,n
        wksp(j)=rb(j)
13    continue
      do 14 j=1,n,2
        rb(j)=wksp(iwksp(j))
	rb(j+1)=wksp(iwksp(j)+1)
14    continue
      do 15 j=1,n
        wksp(j)=rc(j)
15    continue
      do 16 j=1,n,2
        rc(j)=wksp(iwksp(j))
	rc(j+1)=wksp(iwksp(j)+1)
16    continue
      return
      end

C	SUBROUTINE ZITA.F

	subroutine zita(ni,zi,e,ord,tilab,telab)
      implicit double precision (a-h,o-z)
	dimension zi(0:ni)
	dimension telab(ni),tilab(ni)
	pi=3.141592654d00
	R=1.987d-3
	zi(0)=0.d00
	d0=10.d00**ord/4.d00
	do 10 nt=1,ni
	    zi(nt)=d0*tilab(nt)*dexp(-E/R/telab(nt))+zi(nt-1)
10	continue
	return
	end
