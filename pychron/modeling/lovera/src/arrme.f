         IMPLICIT DOUBLE PRECISION (A-H,O-Z)
      parameter(nn=340,nch=1005,ntp=200,pi=3.141592654,
     $xlambd=0.0005543,ro= 1.987d-03,x1=1.2d0,x2=3.d0,acc=1.d-5)
	dimension fe(10,ntp),dzxe(10,ntp),tinv(ntp)
	dimension c(10),af(ntp),zita(ntp)
	dimension t(ntp),f(0:ntp),zx(ntp),dtim(ntp),e(10),d0(10)
	character*9 tab1
	double precision an, bessj0, bessj1, rtsafe
      external an, funcd, bessj0, bessj1, rtsafe
	common /integ/ imod 

	tab1=char(09)
	open(unit=7,file='temstep.in',status='old')
	open(unit=15,file='arr-me.in',status='old')
	open(unit=16,file='arr-me.out',status='unknown')
	open(unit=8,file='each-me.gr',status='unknown')
	open(unit=10,file='arr-me.dat',status='unknown')
	open(unit=1,file='each-me.dat',status='unknown')
	open(unit=11,file='logr-me.dat',status='unknown')
c	open(unit=20,file='test.dat',status='unknown')
	imp = 1
	print *, 'slabs= 1, spheres= 2 , cilinders= 3'
	read *, imod 
	print *, 'model =', imod
      b = 10.d0 - 2.d0 * imod
      if(imod.eq.1)then
         imp = 2
         acut = 0.5
      endif
	if(imod.eq.2)then
	   acut = 0.85
	elseif(imod.eq.3)then
	   acut = 0.6
	endif

	read(15,120)nsamp
	do 11 j=1, nsamp
	  zita(j)=0.
   	  read(15,140)e(j),d0(j),c(j)
	  tc = tc + c(j)
	  d0(j) = 10.**d0(j)
	  if (imod.eq.1) d0(j)=d0(j)/4.
11    continue
	if(abs(tc-1.).gt.1e-8) then
	print *,'Error  -  your concentration c(j) sum ',tc
	stop
	endif
	read(15,*)slop,ord
  120	format(I20)
	read(7,120)nstep
	do 10 nt=1,nstep
	f(nt)=0.
	read(7,*)t(nt),dtim(nt)
	dtim(nt)=60.*dtim(nt)
	do 20 j=1,nsamp
	fe(j,nt)=1.
	zita(j)=d0(j)*dtim(nt)*dexp(-e(j)/ro/t(nt))+zita(j)
	do 30 m=1,40000
	xu=an(m)*zita(j)
	if (xu.gt.99.)goto 20
	fe(j,nt)=fe(j,nt)-b*dexp(-xu)/an(m)
   30	f(nt)=f(nt)-b*c(j)*dexp(-xu)/an(m)
   20	continue
	nnt=nt
	f(nt)=1.+ f(nt)
	if (f(nt).gt..9999)then 
	nnt=nt-1
	goto 40
	endif
   10	continue
   40	continue

c	INVERSION OF THE DATA

 	do 50 k=1,nnt
        if (f(k).le.acut) then
	    if(imod.eq.1)zx(k+1)=pi*(f(k)/4.)**2
	    if(imod.eq.2)zx(k+1)=(2.-pi/3.*f(k)-2.*
     $    dsqrt(1.-pi/3.*f(k)))/pi
          if(imod.eq.3)then
            sb = b**2/pi
            zx(k+1)=((sb-2.d0*f(k))-dsqrt(sb*(sb-4.d0*f(k))))/2.d0
          endif
        else
          zx(k+1)=-dlog(an(1)/b*(1.-f(k)))/an(1)
        endif
          if(imod.eq.3)then
            sb = b**2/pi
            z1=((sb-2.d0*f(k))-dsqrt(sb*(sb-4.d0*f(k))))/2.d0
            z2=-dlog(an(1)/b*(1.-f(k)))/an(1)
c           write(20,*)f(k),z1,z2
          endif

   50   continue
        zx(1)=0.
        do 80 k=1,nnt
        af(k)=(f(k)+f(k-1))/2.*100.
        dzx = dlog10((zx(k+1)-zx(k))/dtim(k)*imp**2)
        tinv(k)=1./t(k)*10000.
        xlogr=(ord-slop*tinv(k)-dzx)/2.
	write(10,110)tinv(k),tab1,dzx
	write(11,110)100.*f(k-1),tab1,xlogr
	write(11,110)100.*(f(k)-0.000001),tab1,xlogr 
  80   write(16,110)tinv(k),tab1,dzx,tab1,f(k)*100.,tab1,xlogr,tab1
     $  ,af(k)
 
	do 200 j=1,nsamp
	do 150 k=1,nnt
	  if (fe(j,k).le.acut) then
	    if(imod.eq.1)zx(k+1)=pi*(fe(j,k)/4.)**2
	    if(imod.eq.2)zx(k+1)=(2.-pi/3.*fe(j,k)-2.*
     $    dsqrt(1.-pi/3.*fe(j,k)))/pi
          if(imod.eq.3)then
            sb = b**2/pi
            zx(k+1)=((sb-2.d0*fe(j,k))-dsqrt(sb*(sb-4.d0*fe(j,k))))/2.d0
          endif
        else
          if (fe(j,k).lt.1.)then
             zx(k+1)=-dlog(an(1)/b*(1.-fe(j,k)))/an(1)
	    else
	      zx(k+1) = 0.
	    endif
        endif

150   continue
      zx(1)=0.
      do 180 k=1,nnt
	if (zx(k+1).gt.0.) then
        dzxe(j,k) = dlog10((zx(k+1)-zx(k))*imp**2/dtim(k))
	endif
  180	continue
  200	continue
	do 195 j=1,nsamp
	do 190 k=1,nnt
	write(8,110)tinv(k),tab1,fe(j,k)
	if (dzxe(j,k).eq.0.)goto 190
        write(1,110)tinv(k),tab1,dzxe(j,k)
  190	continue
	write(8,130)
	write(1,130)
  195	continue

  110	format(1x,5(f12.8,a1))
  130   format(1x,'$')
  140	format(g20.8)
 	end

       double precision function an(m)
       implicit double precision (a-h,o-z)
       parameter(pi=3.14159265,x1=1.2d0,x2=3.d0,acc=1.d-5)
       external funcd
       common /integ/ imod
       if(imod.eq.1)an = ((2*m-1)*pi)**2
       if(imod.eq.2)an = (m*pi)**2
       if(imod.eq.3.and.m.gt.1)then
         den=pi*(4*m-1)
         zero= den/4.+1./(2.*den)-31./(6*den**3)+3779./(15*den**5)
         an = zero**2
       elseif(imod.eq.3)then
         an=rtsafe(funcd,x1,x2,acc)**2
       endif
       return
       end

       subroutine funcd(x1,f,df)
	implicit double precision (a-h,o-z)
           f=bessj0(x1)
           df= - bessj1(x1)
       return
       end

      double precision function bessj0(x)
       implicit double precision (a-h,o-z)
c      real*8 y,p1,p2,p3,p4,p5,q1,q2,q3,q4,q5,r1,r2,r3,r4,r5,r6,
C     *    s1,s2,s3,s4,s5,s6
      data p1,p2,p3,p4,p5/1.d0,-.1098628627d-2,.2734510407d-4,
     *    -.2073370639d-5,.2093887211d-6/, q1,q2,q3,q4,q5/-.1562499995d-
     *1,
     *    .1430488765d-3,-.6911147651d-5,.7621095161d-6,-.934945152d-7/
      data r1,r2,r3,r4,r5,r6/57568490574.d0,-13362590354.d0,651619640.7d
     *0,
     *    -11214424.18d0,77392.33017d0,-184.9052456d0/,
     *    s1,s2,s3,s4,s5,s6/57568490411.d0,1029532985.d0,
     *    9494680.718d0,59272.64853d0,267.8532712d0,1.d0/
      if(dabs(x).lt.8.)then
        y=x**2
        bessj0=(r1+y*(r2+y*(r3+y*(r4+y*(r5+y*r6)))))
     *      /(s1+y*(s2+y*(s3+y*(s4+y*(s5+y*s6)))))
      else
        ax=dabs(x)
        z=8./ax
        y=z**2
        xx=ax-.785398164
        bessj0=dsqrt(.636619772/ax)*(dcos(xx)*(p1+y*(p2+y*(p3+y*(p4+y
     *      *p5))))-z*dsin(xx)*(q1+y*(q2+y*(q3+y*(q4+y*q5)))))
      endif
      return
      end

      double precision function bessj1(x)
	implicit double precision (a-h,o-z)
C      real*8 y,p1,p2,p3,p4,p5,q1,q2,q3,q4,q5,r1,r2,r3,r4,r5,r6,
c     *    s1,s2,s3,s4,s5,s6
      data r1,r2,r3,r4,r5,r6/72362614232.d0,-7895059235.d0,242396853.1d0
     *,
     *    -2972611.439d0,15704.48260d0,-30.16036606d0/,
     *    s1,s2,s3,s4,s5,s6/144725228442.d0,2300535178.d0,
     *    18583304.74d0,99447.43394d0,376.9991397d0,1.d0/
      data p1,p2,p3,p4,p5/1.d0,.183105d-2,-.3516396496d-4,.2457520174d-5
     *,
     *    -.240337019d-6/, q1,q2,q3,q4,q5/.04687499995d0,-.2002690873d-3
     *,
     *    .8449199096d-5,-.88228987d-6,.105787412d-6/
      if(dabs(x).lt.8.)then
        y=x**2
        bessj1=x*(r1+y*(r2+y*(r3+y*(r4+y*(r5+y*r6)))))
     *      /(s1+y*(s2+y*(s3+y*(s4+y*(s5+y*s6)))))
      else
        ax=dabs(x)
        z=8./ax
        y=z**2
        xx=ax-2.356194491
        bessj1=dsqrt(.636619772/ax)*(dcos(xx)*(p1+y*(p2+y*(p3+y*(p4+y
     *      *p5))))-z*dsin(xx)*(q1+y*(q2+y*(q3+y*(q4+y*q5)))))
     *      *dsign(1.d0,x)
      endif
      return
      end

      double precision function rtsafe(funcd,x1,x2,xacc)
        implicit double precision (a-h,o-z)
      parameter (maxit=100)
      call funcd(x1,fl,df)
      call funcd(x2,fh,df)
      if(fl*fh.ge.0.) pause 'root must be bracketed'
      if(fl.lt.0.)then
        xl=x1
        xh=x2
      else
        xh=x1
        xl=x2
        swap=fl
        fl=fh
        fh=swap
      endif
      rtsafe=.5*(x1+x2)
      dxold=dabs(x2-x1)
      dx=dxold
      call funcd(rtsafe,f,df)
      do 11 j=1,maxit
        if(((rtsafe-xh)*df-f)*((rtsafe-xl)*df-f).ge.0.
     *      .or. dabs(2.*f).gt.dabs(dxold*df) ) then
          dxold=dx
          dx=0.5*(xh-xl)
          rtsafe=xl+dx
          if(xl.eq.rtsafe)return
        else
          dxold=dx
          dx=f/df
          temp=rtsafe
          rtsafe=rtsafe-dx
          if(temp.eq.rtsafe)return
        endif
        if(dabs(dx).lt.xacc) return
        call funcd(rtsafe,f,df)
        if(f.lt.0.) then
          xl=rtsafe
          fl=f
        else
          xh=rtsafe
          fh=f
        endif
11    continue
      pause 'rtsafe exceeding maximum iterations'
      return
      end


