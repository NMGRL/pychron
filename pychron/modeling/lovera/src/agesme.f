C	PROGRAM TO CALCULATE AN AGE SPECTRUM FROM A GIVEN THERMAL
C		HISTORY. (AGES.F) (SPHERES) 

C	R= GAS CONSTANT KCAL/(MOL*K)
C	XLAMBD= DECAY CONSTANT OF POTASSIUM IN 1/MYRS.
C	NUSA=# OF SAMPLES,  TOTIME = TOTAL TIME OF Ar ACCUMULATION
C	C40WD= TOTAL ARGON RADIOGENIC 40Ar PRODUCED POR UNIT VOL. FROM TIME=0.
C	C39WD= FRACTION OF 39Ar AT PRESENT.
C	NEND=TIME AT WHICH THE SYSTEM IS EFFECTIVELY CLOSED, TEMPERATURE
C       IS ASSUME CONSTANT FROM THIS TIME UNTIL PRESENT.
C	STEP= DURATION OF THE TIME STEP, PEND AND TEMIN DEFINE
C	 THE DIFFERENT SEGMENTS OF THE COOLING HISTORY
C	NI=# OF HEATING STEPS
C	TELAB = TEMPERATURE STEP (*K), TILAB= DURATION OF THE HEATING STEP (MIN)
C	NSAMP=# OF DIFFERENT DIFFUSION DOMAIN SIZES
C	D0(J)= FREQUENCY FACTOR (1/SEC) 
C	E(J)= ACTIVACTION ENERGY (KCAL/MOL)
C       C(J)= VOLUME FRACION
C	SUBROUTINE GEOSEC CALCULATE THE DISTRIBUTION OF 40Ar AT PRESENT WHICH
C	IS GIVEN BY THE COEFFICIENT XI(N).
C	SUBROUTINE LAB CALCULATE THE RELEASED OF 40Ar and 39Ar AT LAB. 
C	FOR EACH DIFFUSION DOMAIN SIZE. (REA40 AND REA39)
C	CURA= CUMULATIVE RATE OF A40 T0 A39 RELEASE.
C	RATE= STEP RATE OF A40 T0 A39 RELEASE
C	DR39 AND DR40 ARE THE STEP RELEASE OF A39 AND A40 RESPECTIVELY.

C=========================================================================

      implicit double precision (a-h,o-z)
      parameter(nn=340,nch=1005,ntp=100,pi=3.141592654,
     $xlambd=0.0005543,R= 1.987d-03,x1=1.2d0,x2=3.d0,acc=1.d-5)
      dimension r40(ntp),r39(ntp),dr39(ntp)
      dimension temp(nch),time(nch)
      dimension c(10),tra40(0:ntp),tra39(0:ntp),sra40(ntp)
      dimension sra39(ntp),scura(ntp),tilab(ntp),telab(ntp)
	dimension E(10),d0(10),tmin(50),tpin(50)
	double precision zero, bessj0, bessj1, rtsafe
      external zero, bessj0, bessj1, rtsafe
	character*9  tab1, yes*1
	common /var/ an(nn),xi(nn),b,c40
	common /integ/ lc(0:nn),imod

	tab1=char(09)
      open(unit=14,file='ages-me.out',status='unknown')
      open(unit=15,file='agesme.in',status='old')
      open(unit=16,file='ages-me.dat',status='unknown')
      open(unit=17,file='temstep.in',status='old')
      open(unit=19,file='each-me.out',status='unknown')
      open(unit=20,file='chist-me.dat',status='unknown')

      lc(0)=0.
C	CALCULATION OF THE COOLING HISTORY

	read(15,*)np
	do 2 j=1,np
	read(15,*)tmin(j),tpin(j)
	write(20,105)tmin(j),tab1,tpin(j)
2	tpin(j)=tpin(j) + 273.
	write(20,*)'&'
	dt=2
	dtdt=(tpin(1)-tpin(2))/(tmin(1)-tmin(2))
	call chist(np,tmin,tpin,time,temp,dt,ns,nch)
	c40=1.-dexp(-xlambd*tmin(1))
	c39wd=dexp(-xlambd*tmin(1))

      print *, 'If you want to see the CH?, type ''y'''
      read *,yes
      if (yes.eq.'y')stop

	print *, 'slabs= 1, spheres= 2 , cilinders= 3'
	read *, imod 
	print *, 'model =', imod
      b = 10.d0 - 2.d0 * imod

C  DEFINITION OF STEP HEATING SCHEDULED AT LAB.

	read(17,110)ni
	do 12 j=1,ni
   	read(17,*)telab(j),tilab(j)
         if(telab(j).gt.1373.)goto 11
   12	tilab(j)=tilab(j)/5.256e11
   11   ni=j-1
        close(17)

C  DEFINITION OF DISTRIBUTION PARAMETERS

	read(15,110)nsamp
	do 14 js=1,nsamp
	read(15,*)e(js),d0(js),c(js)
        d0(js)= 10.**d0(js)
   14	d0(js)=d0(js)*(24.*3600.*365e06)

C CALCULATION OF LC
      nsq=1
      nsum=0
      m=0
      do 32 j=1,nn-1
	if(nsum.gt.20)then
	  nsum = 1
	  nsq = nsq*2
	endif
	m=m+nsq
	if(m.gt.100)nsum=nsum+1
	lc(j)=m
	if(imod.eq.1)an(j) = ((2*m-1)*pi)**2
      if(imod.eq.2)an(j) = (m*pi)**2
      if(imod.eq.3)an(j) = zero(m)**2       
32    continue
      lc(nn)=lc(nn-1)+1
      if(imod.eq.3)an(1)=rtsafe(x1,x2,acc)**2


C	CALCULATION OF THE AGE SPECTRUM

	do 16 je=1,nsamp	
	if(imod.eq.1)d0(je)=d0(je)/4.d0
	

C	tau=r*550.**2/(e(1)*dtdt)
C      tc= e(1)/r/dlog(8.7*tau*d0(1))-273.

        call geosec(ns,xlambd,d0(je),E(je),temp,time)
        call lab(d0(je),E(je),r40,r39,telab,tilab,dr39,ni,tab1)
 
C	SUMMATION OF THE CONTRIBUTION OF EACH DIFFUSION DOMAIN SIZE.
	
	do 18 k=1,ni
	tra40(k)=c(je)*r40(k)+tra40(k)
   18	tra39(k)=c(je)*r39(k)+tra39(k)
   16	continue
	do 20  j=1,ni
	sra40(j)=tra40(j)-tra40(j-1)
	sra39(j)=tra39(j)-tra39(j-1)
	if (sra40(j).gt.0.and.sra39(j).gt.0)goto  21
	age=0.
	goto 19
   21	continue
  	scura(j)=sra40(j)/sra39(j)
	age=dlog(1.+scura(j)/c39wd)/xlambd
   19	write(16,130)tra39(j-1)*100.,tab1,age
	av=(tra39(j-1)+tra39(j))*50.
	write(14,130)av,tab1,age
C     write(20,105)age,tab1,tc
   20	write(16,130)tra39(j)*100.,tab1,age
	do 22 j=1,ni
	tra39(j)=0.
   22	tra40(j)=0.
  110	format(i20)
  105     format(g20.8,a1,g20.8)
  100	format(g20.8)
  120	format(1x,3(f12.6,a1))
  130	format(1x,3(g20.8,a1))
	stop
	end


      subroutine geosec(nend,xlambd,d0,E,temp,time)
      implicit double precision (a-h,o-z)
      parameter(nch=1005, nn=340, pi=3.141592654,R= 1.987d-03)
      dimension time(nend+4),temp(nend+4),dzita(nch),d(nch)
      common /var/ an(nn),xi(nn),b,c40
	common /integ/ lc(0:nn),imod

	zit=0.
	do 10 j=1,nend
	  avtemp=(temp(j+1)+temp(j))/2.
          if(j.eq.1.and.avtemp.lt.800)then
             print *,"WARNING: the sample could had been"
             print *,"retaining argon at ages >",time(1)," Ma"
             print *,"The program assume zero argon concentration"
             print *,"at the initial age:",time(1)," Ma"
          endif
        d(j)=d0*dexp(-e/r/avtemp)
10	continue	
	dzita(nend+1)=0.
	do 20 j=nend,1,-1
20	dzita(j)=dzita(j+1)+dabs(time(j+1)-time(j))*d(j)
	
C     COMPUTO OF XI(M) - M<80000 --> nn=340
      do 30 mi=1,nn-1
        xlogm=dlog(an(mi))
        sum=0.d0
        do 40 n=1,nend
            if(d(n).eq.0.)goto 40
            uplus=an(mi)*dzita(n+1)+xlambd*(time(1)-time(n+1))
            if (uplus-xlogm.gt.25.)goto 40
              al=an(mi)*d(n)-xlambd
              xal= al *(time(n)-time(n+1))
              if (dabs(xal).gt.30)then
                    camal=1.d0/al
              else
                    if (dabs(xal).gt.0.001)then
                        camal=(1.d0-dexp(-xal))/al
                   else
                       camal=(time(n)-time(n+1))*(1-xal/2+xal**2/6.d0)
                   endif
              endif
            sum=sum+d(n)*dexp(-uplus)*camal
40        continue
          tzita = dzita(1)*an(mi)
          if(tzita.lt.30.)then
               xfact = dexp(-tzita)
          else
               xfact = 0.d0
          endif
          xi(mi)=sum*an(mi) + xfact
30    continue
80    continue
      return
      end
      
      subroutine lab(d0,e,r40,r39,telab,tilab,dr39,ni,tab1)
      implicit double precision (a-h,o-z)
      parameter(nn=340,ntp=200,pi=3.141592654,xlambd=0.0005543,
     $R=1.987d-03)
      dimension r40(ni),zita(ntp),r39(ni),ages(ntp)
      dimension dr39(ni),dr40(ntp),rate(ntp),tilab(ni),telab(ni)
      character*9 tab1
      common /var/ an(nn),xi(nn),b,c40
	common /integ/ lc(0:nn),imod


	c39wd=1-c40
	zii=0.
	do 10 nt=1,ni
   	zita(nt)=zii+d0*tilab(nt)*dexp(-e/(r*telab(nt)))
   10	zii=zita(nt)
   
	do 20 j=1,ni
	  r39(j)=1.
	  r40(j)=0.
	  sumck = 0.
        do 20 k=1,nn-1
          xmat=0.d0
          do 22 k1=lc(k-1)+1,lc(k)-1
             if(imod.eq.1)an2 = ((2*k1-1)*pi)**2             
             if(imod.eq.2)an2 = (k1*pi)**2
             if(imod.eq.3)an2 = zero(k1)**2       
	       if (zita(j)*an2.gt.100.) then
	          ab = 0.
	       else
	          ab= dexp(-zita(j)*an2)/an2
		 endif
		 xmat= xmat+(1.d0-(lc(k)-k1)/(lc(k)-lc(k-1)))*(1./an2-ab)             
22	    continue
          do 24 k1=lc(k),lc(k+1)-1
             if(imod.eq.1)an2 = ((2*k1-1)*pi)**2
             if(imod.eq.2)an2 = (k1*pi)**2
             if(imod.eq.3)an2 = zero(k1)**2 
             if(imod.eq.3.and.k1.eq.1)an2=an(1)      
	       if (zita(j)*an2.gt.100.) then
	          ab = 0.
	       else
	          ab= dexp(-zita(j)*an2)/an2
   		    r39(j)=r39(j)-b*ab
		 endif
		 sumck = sumck + b*1.d0/an2
		 xmat= xmat+(lc(k+1)-k1)/(lc(k+1)-lc(k))*(1./an2-ab)
             r40(j)=r40(j)+b*(c40-1)*(1./an2-ab)
24	    continue
             r40(j)=r40(j)+b*xmat*xi(k)
   20	continue
	rate(1)=r40(1)/r39(1)
	dr39(1)=r39(1)
	dr40(1)=r40(1)
	do 50 j=2,ni
	dr39(j)=r39(j)-r39(j-1)
   	dr40(j)=r40(j)-r40(j-1)
	if (dr39(j).gt.0.and.dr40(j).gt.0)goto 70
	ages(j)=0.
	goto 50
   70   rate(j)=dr40(j)/dr39(j)
   	ages(j)=dlog(1.+rate(j)/c39wd)/xlambd
   50 	continue
	ages(1)=dlog(1.+rate(1)/c39wd)/xlambd
	rnum = 1. - 1.0e-07
	do 80 j=1,ni
	if(r39(j).le.rnum)then
   	write(19,140)r39(j)*100,tab1,ages(j)
	endif
   80 	continue
  140	format(1x,4(f12.4,a1))
	return
	end

C	SUBROUTINE TO CALCULATE THE THERMAL HISTORY.
C		 (SUBROUTINE SUBCHIST.F)

        subroutine chist(np,tmin,tpin,time,temp,dt,ns,nch)
        implicit double precision (a-h,o-z)
        dimension temp(nch),time(nch)
        dimension tpin(np),tmin(np)
        CHARACTER TAB1*9
        TAB1=CHAR(09)
	open(unit=18,file='chist.dat')

c	DEFINITION OF THE TEMPERATURE STEP IN CENTIDEGREE.


C	CALCULATION OF THE COOLING HISTORY

        ns=0.
	temp(1)=tpin(1)
        time(1)=tmin(1)
	tem0=tpin(1)
     	do 4 k=1,np-1
	   nt=dabs(tpin(k)-tpin(k+1))/dt + ns
	   snt=(tpin(k)-tpin(k+1))
	   if(dabs(snt).lt.dt)then
	     	temp(nt+2)=tpin(k+1)
		time(nt+2)=tmin(k+1)
	        ns = ns + 1
		tem0=tpin(k+1)
		goto 4
            endif
	   snt=snt/dabs(tpin(k)-tpin(k+1))
	   do 6 j=ns+2,nt+1
	     temp(j)=tem0 - snt*dt
	     time(j)= age(temp(j),tmin(k),tmin(k+1),tpin(k),tpin(k+1))
	     tem0 = temp(j)
6	   continue
	   ns = nt
	   if(dmod(tpin(k)-tpin(k+1),dt).ne.0.)then
		temp(nt+2)=tpin(k+1)
		time(nt+2)=tmin(k+1)
	        tem0=temp(nt+2)
	        ns = ns + 1
           endif
           if(ns.gt.nch-2)stop 'Number of step larger than 1000'
4	continue

	do 8 jk=1,ns+1
            write(18,100)time(jk),tab1,temp(jk)-273.
8	continue
100     format(g20.8,a1,g20.8)
	return
	end

      double precision function age(y,a1,a2,t1,t2)
      implicit double precision (a-h,o-z)
      if(y.lt.0.)pause 'temperature less than zero'
          age=a1 + (y - t1)*(a2-a1)/(t2-t1)
        return
      end

       double precision function zero(n)
       implicit double precision (a-h,o-z)
       parameter(pi=3.14159265)
          den=pi*(4*n-1)
         zero= den/4.+1./(2.*den)-31./(6*den**3)+3779./(15*den**5)
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

      double precision function rtsafe(x1,x2,xacc)
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
