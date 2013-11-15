C	NEWARR2.F
C       ERROR ON BOTH AXIS  - USES OLD RAMDOM ROUTINE GUESS
C	TO USE NEW RAMDOM ROUTINE GUESS0 UNCOMMENT THE CALL GUESS0
C	AND COMMENT OUT THE CALL TO GUESS
C	FROM AUTOTEST DIR
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
  
C       "INPUT FILES"           "UNIT"          "PROGRAM"  
C         SAMPLES.LST              8              MAIN  
C         TEMSTEP.IN (*.tmp)      10              MAIN  
C         FJ.IN      (*.fj)       12              MAIN  
C         AR39       (*.ar3)      14              MAIN  
  
C       "OUTPUT FILES"          "UNIT"          "PROGRAM"  
C         ARR.DAT   (*.ar1)       16              ARR  
C         LOGR.DAT  (*.lg1)       18              ARR  
C         ARR.SAMP  (*.ar0)       20              DIFF  
C         LOGR.SAMP (*.lg0)       22              DIFF  
C         SIZES.DAT               24              MAIN  
C         VOLCON.DAT              26              MAIN  
C         PARAM.OUT (*.par)       28              MAIN  
C         ARR-ME.IN (*.ame)       30              MAIN  
C         DIST.DAT  (*.dst)       32              MAIN  
C         ENER.DAT                34              PARAM  
C         INFO.DAT                36              MAIN
  
C ***********************************************************************  
  
      implicit double precision (a-h,o-z)  
      parameter(nca=20,ns=200,r=1.987E-3,pi=3.141592654)
      parameter(ee=0.4342944879)  
      dimension a1(nca),a2(nca),auxal(nca,nca),auxa2(nca)  
      dimension auxa1(nca),dyda(nca),zi(0:ns),wt(ns),fmod(0:ns)  
      dimension covar(nca,nca),alpha(nca,nca),lista(nca),da(nca)  
      dimension wksp(nca),iwksp(nca),orde(20),wf(ns),dzx(ns)  
      common /var/ f(0:ns),telab(ns),tilab(ns),xlogd(0:ns),sig39(ns),  
     $xlogr(0:ns),a39(ns),acut,b,sige,sigo,qmax,chisqe  
      common /int/ ni,imp,nimax,ke  
      character  tab1*9,sname*50,yes*1,yes1*1 
      tab1=char(09)  
  	iseed = -3      
	iflag = 0
	kctotal = 0
	open(unit=34,file='energy.dat')  
      open(unit=24,file='sizes.dat')  
      open(unit=26,file='volcon.dat') 

	print *,'Enter # of points in E-gaussian distribution (Max.=10)'
	read *,ngauss
2	print *,'Would you like to enter samples from list (yes/no)?'
	read *,yes
      if(yes.eq.'y')then
	  print *,'Enter filename that contains the list of samples'
	  read(*,'(a50)')sname
	  kn=name(sname) 
	  open(unit=8,file=sname(1:kn),status='old',ERR=2)
      endif
1	if(yes.eq.'y')then
          read(8,102,END=300)sname
        else
	  print *,'Enter sample name (stop to exit)'
	  read *,sname
	  if(sname(1:4).eq.'stop')stop
	endif
      kn=name(sname)  
	kd=kd+1  
      open(unit=10,file=sname(1:kn)//'_tmp.in',status='old')  
      open(unit=12,file=sname(1:kn)//'_fj.in',status='old')  
      open(unit=14,file=sname(1:kn)//'_a39.in',status='old')  
      open(unit=16,file=sname(1:kn)//'.ar1')  
      open(unit=18,file=sname(1:kn)//'.lg1')  
      open(unit=20,file=sname(1:kn)//'.ar0')  
      open(unit=22,file=sname(1:kn)//'.lg0')  
      open(unit=28,file=sname(1:kn)//'.par')  
      open(unit=30,file=sname(1:kn)//'.ame')  
      open(unit=32,file=sname(1:kn)//'.dst')
      nloop = 1 
      f(0) = 0.  
      zi(0)=0.  
      b=8.  
      imp=2.  
      acut = 0.5  
      dchmin = 0.01  
      ncons = 0  
      ndom = 8  
      mdom = 8  
      read(10,120)ni  
      nimax = ni  
      do 10 nt=1,ni  
        read(10,100)telab(nt),tilab(nt)  
        read(12,*)f(nt)  
	  read(14,*)a39(nt),sig39(nt)
        if(f(nt).gt.0.2.and.nt.eq.1)then  
          read(12,*)f(nt)  
          read(12,*)f(nt)  
        endif  
        tilab(nt)=60.*tilab(nt)  
        if(ni.eq.nimax.and.telab(nt).gt.1373)nimax = nt-1  

10    continue  
      call diff(ord,E,wt,xro)  
      call weight(wf)  
      close(20)  
      print *, sname
      print *, 'E=',e,' +- ',sige,'     Ordinate=',ord,' +-',sigo 

      if(yes.eq.'y'.and.iflag.eq.0)then
	   iflag = -1
	   print *
         print *, 'Do you want to calculate all the samples'
         Print *, 'with a single set of e and Do values?'
         read *, yes1
	   if(yes1.eq.'y')then
	      print *,'enter E (kcal/mol)'
            read *,e1
            print *, 'enter uncertainty in E'
            read *, sige1
            print *,'enter ordinate = log(Do/ro2)'
            read *,ord1
            print *, 'enter uncertainty in ordinate'
            read *, sigo1
	   endif 
	elseif(yes.ne.'y')then
         print *, 'do you want to modify the e and Do values?'
         read *, yes 
         if(yes.eq.'y')then
            print *,'enter E (kcal/mol)'
            read *,e
            print *, 'enter uncertainty in E'
            read *, sige
            print *,'enter ordinate = log(Do/ro2)'
            read *,ord
            print *, 'enter uncertainty in ordinate'
            read *, sigo
            print *, 'E=',e,' +- ',sige,'     Ordinate=',ord,' +-',sigo 
         endif
         yes='n'
      endif
	if(yes1.eq.'y')then
	   e=e1
	   sige = sige1
	   ord = ord1
	   sigo = sigo1
         print *, 'E=',e1,'+-',sige1,'  Ordinate=',ord1,'+-',sigo1 
	endif
      write(28,*)sname
	write(28,*)'E=',e,'+-',sige,'     Ordinate=',ord,'+-',sigo 
      e0 = e
      ord0 = ord 
      write(28,*)  
      ni = nimax 
c  HERE STARTS LOOP FOR GAUSSIAN E.
5     call zita(zi,e,ord)  
      ckchisq=1.0e30  
      ckchin = 1.0e30  
      mct = 0    
70    call guess(ndom,a1,a2,xro,iseed) 
      if(mct.gt.30) then  
        write(28,*) 'Warning: Too many iterations,  
     $  Consult your computer vodoo',sname(1:kn),ncicle
        if(ncicle.gt.0)ncicle=4
        amax=0.  
        mct=0  
        chisq=1.0e30  
        goto 54  
      endif  
      nc = 0  
      na = 2.*ndom -1  
      do 12 j=1,na  
12    lista(j)=j  
      mfit = na  
      if(ncons.eq.1)mfit = na-1  
      alamda = -1.  
      kc=0.  
      ch = -1.  
      alam = 0.001  
26    call mrqmin(zi,f,wf,ni,a2,na,lista,mfit,covar,alpha,  
     $nca,chisq,alamda,amax) 
      kctotal = kctotal + 1 
      do 52 j=1,na,2  
         if(a2(j+1).lt.-14)then  
             amax=-1.  
         endif  
      do 52 k=1,na,2  
         if(j.eq.k) goto 52  
         if(a2(j).eq.a2(k))then  
              amax=-1  
         endif  
52    continue  
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
84    write(28, *)'# dom=',ndom,'  Isteps=',kc,'  mct=',mct,  
     $'   nc=',nc,'   chisq=',chisq  
      goto 54  
72    alamda = 0.  
      ndom = (na+1)/2  
      call mrqmin(zi,f,wt,ni,a2,na,lista,mfit,covar,  
     $alpha,nca,chisq,alamda,amax)
      if(amax.eq.-1.) then  
        mct = mct + 1  
        goto 70  
      endif
      do 24 nt=1,ni  
         call funcs(zi(nt),a2,y,dyda,na,a1,amax)  
         fmod(nt) = y  
         if(amax.eq.-1)stop 'stop 3: Consult your vodoo'  
   24 continue  
      call sort3(2*ndom,a1,a2,da,wksp,iwksp)  
      rpmax = a1(na)  
      xlog = ord - 2.* dlog10(rpmax)  
      write(30,120)ndom  
      write(28,140)  
      sc = 0. 
      kd = 8  
      do 28 j=1,na+1,2  
        write(30,100)e  
        orde(j)=xlog - 2.*dlog10(a1(j)/rpmax)  
        write(30,100)orde(j)  
        write(30,105)a1(j+1)  
        write(28,115)(j+1)/2,a1(j+1),a1(j)/rpmax  
        if(f(nimax).gt.sc.and.f(nimax).lt.sc+a1(j+1))kd=(j+1)/2  
        sc = sc + a1(j+1)  
28    continue  
      write(24,116)sname(1:kn),tab1,(orde(k),k=1,na+1,2),kd  
      write(26,116)sname(1:kn),tab1,(a1(k+1),k=1,na+1,2)  
      write(28,*)  
      write(28,*)ckchisq  
      slop = e*ee/10000./r  
      write(30,*)slop  
      write(30,*)ord  
      call arr(e,ord,dzx,fmod)  
      chisq2 = 0.d0  

      noutlier = 0  
      do 55 i=1,nimax  
          dy1 = dabs((xlogd(i)-dzx(i))/wt(i))  
         if(dy1.lt.4)then  
            chisq2=chisq2+ dy1**2  
         else  
           noutlier = noutlier + 1  
         endif  
55    continue  
      q=gammq(0.5d0*(nimax-2),0.5*chisq2)  
      write(34,180)sname(1:kn),tab1,e,tab1,sige,tab1,ord,tab1,  
     $sigo,tab1,ke,chisq2,q,nimax,noutlier  
c      write(16,*)'&'
c      write(18,*)'&'
      write(30,*)'&'

c ENTER HERE CODE FOR GAUSSIAN E DISTRIBUTION
      if(nloop.lt.ngauss)then
	    write(28,*)'  kctotal = ',kctotal
	    write(28,*)
	    kctotal = 0
	    nloop = nloop + 1
	    call stats(E0,sige,ord0,sigo,E,ord,iseed)
		write(28,*)'E=',e,'  Ordinate=',ord
	    goto 5
	endif
	close(unit=10)  
      close(unit=12)  
      close(unit=14)  
      close(unit=16)  
      close(unit=18)  
      close(unit=20)  
      close(unit=22)  
      close(unit=28)  
      close(unit=30)  
      close(unit=32)
      if(yes.eq.'y')goto 1
      stop 'End of sample calculation'  
54    continue  
      if(ckchisq.gt.chisq) then  
         do 64 j=1,na+1  
            auxa2(j)=a2(j)  
         do 64 k=1,na+1  
            auxal(j,k)=alpha(j,k)  
64       continue  
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
            write(32,*)sumc,log(auxa1(j))  
            sumc = sumc + auxa1(j+1)  
            write(32,*)sumc,log(auxa1(j))  
68       continue  
         if(ndom.eq.mdom-1)then  
            do 66 j=1,auxna+1  
                 a2(j)=auxa2(j)  
            do 66 k=1,auxna+1  
                 alpha(j,k)=auxal(j,k)  
66          continue  
            na = auxna  
            mfit = na  
            if(ncons.eq.1)mfit=na-1  
            amax = 0.  
            goto 72  
         endif  
      endif  
      goto 70  
38    ch = chisq  
      alam = alamda  
      goto 26  
  300 stop 'end iteration'  
  100 format(G20.8)  
  102 format(A50)  
  105 format(f12.8)  
  110 format(1X,5(F12.8,A1))  
  115 format(1X,I4,3x,f9.5,7x,f12.8)  
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
  
C	SUBROUTINE ARR.F  
C **********************************************************************  
C       "PARAMETERS"  
C	R= GAS CONSTANT KCAL/(MOL-K)  
C       D0= FREQUENCY FACTOR (1/SEC)  
C       "INPUT"  
C	NUSA=# OF SAMPLES   
C	NSAMP=# OF DIFFERENT DIFF. DOMAINs  
C       E= ACTIVATION ENERGY (KCAL/MOL)  
C	ORD = LOG (Doi/Ro**2)  
C       C(J)= VOL. FRAC. OF Jth DOMAIN  
C	RP(J)= PLATEAU SIZE (LOG(R/Ro) PLOT)  
C	NI=# OF HEATING STEPS  
C	TELAB = TEMP. STEP (K)  
C       TILAB= STEP HEATING DURATION (MIN)  
C       "OUTPUT"  
C	TINV = INVERSE LAB. TEMP. (10000/K)  
C	DZX = - LOG(D/R**2) (1/SEC)  
C	F(J)*100 = CUMULATIVE % 39-AR RELEASED   
C	AVT = (F(J)+F(J-1))*50  
C	XLOGR= LOG(R/Ro)  
C	RAD(J) = SIZE OF THE Jth DIFF. DOMAIN  
C       C(J) = VOL. FRAC. OF Jth DOMAIN  
C ***********************************************************************  
      subroutine arr(e,ord,dzx,fmod)  
      implicit double precision (a-h,o-z)  
      parameter(ns=200,r=1.987E-3,pi=3.141592654,ee=0.4342944879)  
      dimension dzx(ns),zx(ns),fmod(0:ns)  
      common /var/ f(0:ns),telab(ns),tilab(ns),xlogd(0:ns),sig39(ns),  
     $xlogr(0:ns),a39(ns),acut,b,sige,sigo,qmax,chisqe  
      common /int/ ni,imp,nimax,ke  
      character  tab1*9  
      tab1=char(09)  
C     INVERSION OF 39-F  
      do 20 k=1,ni  
        if (fmod(k).gt.acut) then  
           zx(k+1)=-dlog(pi**2/b*(1.-fmod(k)))/pi**2  
        else  
           zx(k+1)=pi*(fmod(k)/4.)**2  
        endif  
   20 continue  
      zx(1)=0.  
      slop=E*ee/10000./R  
      do 26 k=1,ni  
        dzx(k) = dlog10((zx(k+1)-zx(k))/tilab(k)*imp**2)  
        tinv=1./telab(k)*10000.  
        xlog=(ord-slop*tinv-dzx(k))/2.  
        write(18,110)fmod(k-1)*100.,tab1,xlog  
        write(18,110)fmod(k)*100.,tab1,xlog  
   26 write(16,110)tinv,tab1,dzx(k)  
      write(16,*)'&'  
      write(18,*)'&' 
        do 30 k=1,ni 
          tinv=1./telab(k)*10000. 
          xlogr0=(ord-slop*tinv-xlogd(k))/2.  
          write(22,110)f(k-1)*100.,tab1,xlogr0  
          write(22,110)f(k)*100.,tab1,xlogr0 
30      continue   
        write(22,*)'&'
  110 format(1X,5(F12.8,A1)) 
      return  
      end  
  
C       SUBROUTINE DIFF.F
C	SUBROUTINE PARAM.F  
C  	SUBROUTINES FIT, GSER, and GCF  - FUNCTIONS GAMMQ and GAMMLN  
  
      subroutine diff(ord,E,wt,xro)  
      implicit double precision (a-h,o-z)  
      parameter(ns=200,r=1.987E-3,pi=3.141592654,ee=0.4342944879)  
      dimension tinv(ns),wt(ns)  
      common /var/ f(0:ns),telab(ns),tilab(ns),xlogd(0:ns),sig39(ns),  
     $xlogr(0:ns),a39(ns),acut,b,sige,sigo,qmax,chisqe  
      common /int/ ni,imp,nimax,ke  
      character tab1*9  
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
         write(20,110)tinv(k),tab1,xlogd(k),tab1,wt(k)  
20    continue  
   
C     CALCULATION OF E AND Do/Ro^2  
      call param(tinv,wt,e,ord)  
      slop = e*ee/(r*10000)  
      xro = (ord-slop*tinv(nix)-xlogd(nix))/2.*(1.+ (1.-f(nix))/2.)  
      return  
110   format(1X,5(F12.8,A1))  
      end  
  
C     SUBROUTINE PARAM.F  
      subroutine param(tinv,wt,e,ord)  
      implicit double precision (a-h,o-z)  
      parameter(ns=200,r=1.987E-3,pi=3.141592654,ee=0.4342944879  
     $,nstop=20,mwt=1,dtp=5.d0)  
      dimension tinv(ns),wt(ns),y(ns),alog(ns),x1(ns),y1(0:ns),wty(ns)  
     $,wtx(ns)  
      common /var/ f(0:ns),telab(ns),tilab(ns),xlogd(0:ns),sig39(ns),  
     $xlogr(0:ns),a39(ns),acut,b,sige,sigo,qmax,chisqe  
      common /int/ ni,imp,nimax,ke  
      character tab1*9  
      tab1=char(09)
	iflag2 = 0  
      nst = nstop  
      y(3)=0.  
      if(ni.lt.nstop) then  
         nst = ni  
      endif  
      ki=0  
15    qmaxk = 0.  
      qmax=1.  
      sx1=0.  
      do 12 j=1,3  
           x1(j)=tinv(ki+j)  
           sx1 = sx1 + x1(j)  
           y1(j)=xlogd(ki+j)  
           wty(j)=wt(ki+j)  
           wtx(j)=10000.d0*dtp/telab(ki+j)**2  
12    continue  
      do 10 k=4,nst  
        x1(k)=tinv(ki+k)  
        sx1 = sx1 + x1(k)  
        y1(k)=xlogd(ki+k)  
        wty(k)=wt(ki+k)  
        wtx(k)=10000.d0*dtp/telab(ki+k)**2  
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
        if(q/qmax.lt.1.e-10.and.k.gt.8.and.iflag2.eq.-1)goto 24  
        y(k) = -r*bf*10000./ee  
        alog(k) = a  
        sige1 = r*sigb*10000./ee  
        qs=k*q  
        if(qs.gt.qmaxk.and.ncont.ge.3)then 
	    iflag2 = -1 
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
  
C   SUBROUTINE FUNCS  
      Subroutine funcs(x,b,y,dyda,na,a,amax)  
      implicit double precision (a-h,o-z)  
      parameter (nmax=21,pi = 3.141592654)  
      dimension a(na+1),dyda(na+1),b(na+1),csh(nmax)  
c  THE MULTIPLICATION BY 4 STAND BY THE DIVITION OF D0  
      if(na.eq.0)return  
      y= 0.  
      as = 1. 
      do 5 j=1,na,2  
          a(j) = dexp(b(j))     
          a(j+1) = (1. + dtanh(b(j+1)))/2.  
          csh(j+1) = 0.5/dcosh(b(j+1))**2   
          as=as - a(j+1)  
   5  continue  
      a(na+1) =as + a(na+1)  
      if(a(na+1).lt.1.d-14)then  
           a(na+1)= 1.d-14  
      endif  
      b(na+1) = dlog(a(na+1))  
      do 10 i=1,na,2  
        arg = x/a(i)*4. 
	  if(arg.lt.0)then
	     stop 'arg less than zero'
	  endif 
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
   20   dgf = dgf + 2. *  dexp(-arg1)  
   21   y = y + a(i+1) * gf  
        dyda(i+1)= gf  * csh(i+1)  
        dyda(i) = -a(i+1) * dgf * arg  
        a(i)=dsqrt(a(i))  
   10 continue  
      return  
      end  
  
C       SUBROUTINE GUESS.F  
	subroutine guess(ndom,a1,a2,xro,iseed)  
        implicit double precision (a-h,o-z)  
	dimension a1(2*ndom),a2(2*ndom)  
  
C     SUBROUTINE TO GUESS C(J),R(J)  
      na=2*ndom  
      sum = 0.  
c  Definition of volume concentration
      do 8 j=1,na,2  
        a1(j+1)= 1. + 10. * ran1(iseed)  
        sum = sum + a1(j+1)  
8     continue 
c  Normalization of volume concentration 
      do 9 j=1,na,2  
        a1(j+1)= a1(j+1)/sum  
9     continue  
c  Definition of sizes (start with random order numbers greater to smaller)
      sum =0  
      do 10 j=1,na-2,2  
        sum= 1 + 10. * ran1(iseed) + sum  
        a1(na-2-j) = sum  
10    continue  
c   Normalized to max log(r/ro) value xro, a1(1)=xro
      do 11 j=1,na-2,2  
        a1(j) = a1(j)/sum * xro  
11    continue  
      sum = a1(na)+a1(na-2)  
      do 12 j=3,na-3,2  
        a1(j) = a1(j) - dlog10(sum)  
        sum = sum + a1(na-(j+1))  
12    continue  
C  'ro' IS THE INVERSE OF Ro (1/Ro)  
      ro = 10.**(a1(1))  
      do 15 j=3,na-3,2  
        a2(j)=a1(1)-a1(na-j)  
15    continue  
      do 17 j=3,na-3,2  
        a1(j)=a2(j)  
17    continue  
      a1(na-1)=dlog10(a1(na))  
      do 20 j=1,na-3,2  
        a1(j)=a1(j+1)/(10.**a1(j)-10.**a1(j+2))  
20    continue  
      a1(na-1)=1.  
      nloop = 0  
29    continue  
      ncont = 0  
      nloop = nloop + 1  
      do 35 j=1,na-3,2  
        rom = 0.  
        if (a1(j).gt.1.) stop 'a1(j) > 1.'  
        if(a1(j+2).lt.a1(j))then  
          ncont = 0  
          do 27 k=j,j+2,2  
             rom = rom + a1(k+1)/a1(k)  
27        continue  
          a1(j+2) = a1(j)  
          a1(j) = a1(j+1)/(rom - a1(j+3)/a1(j+2))  
        else  
          ncont = ncont + 1  
          endif  
35    continue  
      if (nloop.gt.30) stop 'nloop greater than 30 on guess'  
      if (ncont.lt.(ndom-1)) goto 29  
      sumro = 0.  
      do 30 j=1,na-1,2  
        sumro = sumro + a1(j+1)/a1(j)  
30    continue  
C   CALCULATION OF A2  
      do 25 j=1,na-1,2  
        a2(j)=2.*dlog(a1(j)*ro)  
        z = 2. * a1(j+1) - 1.  
        a2(j+1) = 0.5 * dlog((z+1)/abs(z-1))  
25    continue  
      return  
      end  
  
C       SUBROUTINE GUESS0.F  
      subroutine guess0(ndom,a1,a2,xro,iseed)  
      implicit double precision (a-h,o-z)  
      dimension a1(2*ndom),a2(2*ndom)  
      na=2*ndom  
      sum = 0.  
      ro = 10.d0**xro  
      do 8 j=1,na,2  
        a1(j+1)= 1. + 10. * ran1(iseed)  
        sum = sum + a1(j+1)  
8     continue  
      do 9 j=1,na,2  
        a1(j+1)= a1(j+1)/sum  
9     continue  
      sum =0.d0  
      sum2 = 0.d0  
      a1(na-1)=1.d0  
      do 10 j=1,na-3,2  
        fact = ro*2.**((j-na+3)/2)  
        a1(j)= 1.d0 + fact * ran1(iseed)   
        sum = sum + a1(j)  
        sum2 = sum2 + 1.d0/a1(j)   
10    continue  
      do 11 j=1,na-3,2  
        a1(j) = a1(j) * a1(j+1) * sum2/(ro-a1(na))  
11    continue  
c	SORT A1(J)      
      do 12 j=3,na-3,2  
         a=a1(j)  
         b=a1(j+1)  
        do 15 i=j-2,1,-2  
          if(a1(i).le.a)goto 17  
          a1(i+2)=a1(i)  
          a1(i+3)=a1(i+1)  
15      continue  
        i=-1          
17      a1(i+2)=a  
        a1(i+3)=b  
12    continue  
  
C   CALCULATION OF A2  
      do 25 j=1,na-1,2  
        a2(j)=2.*dlog(a1(j)*ro)  
        z = 2. * a1(j+1) - 1.  
        a2(j+1) = 0.5 * dlog((z+1)/abs(z-1))  
25    continue  
      return  
      end  
  

  
C  SUBROUTINE INDEXX  
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
  
C       SUBROUTINES MRQMIN,MRQCOF, GAUSSJ, COVSRT  
  
  
      subroutine mrqmin(x,y,sig,ndata,a,ma,lista,mfit,  
     *  covar,alpha,nca,chisq,alamda,amax)
	implicit double precision (a-h,o-z)  
      parameter (mmax=20)  
      dimension x(0:ndata),y(0:ndata),sig(ndata),a(ma+1),lista(ma),  
     *  covar(nca,nca),alpha(nca,nca),atry(mmax),beta(mmax),da(mmax) 
        save beta,atry,da,ochisq 
	amax = 0.  
	do 25 j=1,ma,2  
	    if(dabs(2*a(j)).gt.amax)amax=dabs(2.d0*a(j))  
25	continue 
      if(amax.gt.30.)amax=30.d0 
      if(alamda.lt.0.)then  
	  iseed = 1
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
     *,amax)  
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
	do j=1,mfit,2
	  if(dabs(da(j)).gt.8)da(j)=sign(8.,da(j))
	  if(dabs(da(j+1)).gt.3)da(j+1)=sign(3.,da(j+1))
	enddo
      if(alamda.eq.0.)then  
        call covsrt(covar,nca,ma,lista,mfit)  
        return  
      endif  
21	sum = 0.  
      do 16 j=1,mfit  
        atry(lista(j))=a(lista(j))+da(j) 
	  if(j/2*2-j.eq.0.and.atry(lista(j)).lt.-5)then
           atry(lista(j))=-5 
	  endif
	  if(j/2*2-j.ne.0.and.dabs(atry(lista(j))).gt.14)then
           atry(lista(j))=sign(14.,atry(lista(j))) + ran1(iseed)
	  endif
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
20	 continue  
	 goto 21  
       endif  
	  
      call mrqcof(x,y,sig,ndata,atry,ma,lista,mfit,covar,da,nca,chisq  
     *,amax)  
	if(amax.eq.-1)return  
      if(chisq.le.ochisq)then  
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
  
      subroutine zita(zi,e,ord)  
      implicit double precision (a-h,o-z)  
      parameter(nca=20,ns=200,r=1.987E-3,pi=3.141592654,ee=0.4342944879)  
      dimension zi(0:ns)  
      common /var/ f(0:ns),telab(ns),tilab(ns),xlogd(0:ns),sig39(ns),  
     $xlogr(0:ns),a39(ns),acut,b,sige,sigo,qmax,chisqe  
      common /int/ ni,imp,nimax,ke  
      zi(0)=0.d00  
      d0=10.d00**ord/4.d00  
      do 10 nt=1,ni  
          zi(nt)=d0*tilab(nt)*dexp(-E/R/telab(nt))+zi(nt-1)  
10    continue  
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
         sigat = sigat + sigsm(i)**2  
         sigf(i)=sigat   
10    continue  
C  CALCULATION OF SIGMA DELTA XI  
      do 30 i=1,ni  
         if (f(i).le.acut) then  
            fp = f(i)+f(i-1)  
            as1 = 1.d0/fp**2-2.d0/fp  
            as2 = (f(i)**2-2*f(i)*(f(i)**2-f(i-1)**2))/fp**2  
            sigzit(i) = 4.d0*(sigat + sigf(i-1)*as1+siga(i)**2*as2)  
         else  
            dzit2 = (dlog((1-f(i))/(1-f(i-1)))/an1)**2  
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

C     Compute samples from normal distribution with mean of 0 and 
C       standard deviation of 1; based on the Box-Muller Transformation.

      double precision function gasdev(idum)
      implicit double precision (a-h,o-z)
      data iset/0/
      if (iset.eq.0) then
1       v1=2.*ran1(idum)-1.
        v2=2.*ran1(idum)-1.
        r=v1**2+v2**2
        if(r.ge.1.)go to 1
        fac=sqrt(-2.*dlog(r)/r)
        gset=v1*fac
        gasdev=v2*fac
        iset=1
      else
        gasdev=gset
        iset=0
      endif
      return
      end

      double precision function ran1(idum)
      dimension r(97)
      save ix1,ix2,ix3,r
      parameter (m1=259200,ia1=7141,ic1=54773,rm1=3.8580247e-6)
      parameter (m2=134456,ia2=8121,ic2=28411,rm2=7.4373773e-6)
      parameter (m3=243000,ia3=4561,ic3=51349)
      data iff /0/
      if (idum.lt.0.or.iff.eq.0) then
        iff=1
        ix1=mod(ic1-idum,m1)
        ix1=mod(ia1*ix1+ic1,m1)
        ix2=mod(ix1,m2)
        ix1=mod(ia1*ix1+ic1,m1)
        ix3=mod(ix1,m3)
        do 11 j=1,97
          ix1=mod(ia1*ix1+ic1,m1)
          ix2=mod(ia2*ix2+ic2,m2)
          r(j)=(float(ix1)+float(ix2)*rm2)*rm1
11      continue
        idum=1
      endif
      ix1=mod(ia1*ix1+ic1,m1)
      ix2=mod(ia2*ix2+ic2,m2)
      ix3=mod(ia3*ix3+ic3,m3)
      j=1+(97*ix3)/m3
      if(j.gt.97.or.j.lt.1)then
          pause
      endif
      ran1=r(j)
      r(j)=(float(ix1)+float(ix2)*rm2)*rm1
      return
      end

	  subroutine stats(xval,xerr,yval,yerr,xran,yran,idum)
      implicit double precision (a-h,o-z)
      parameter(rt=0.938)
      rt1 = sqrt(1.0-(rt**2))
      gnoise1 = gasdev(idum)
      xran = xval + xerr*gnoise1 
      gnoise2 = gasdev(idum) 
      yran = yval + yerr*(rt*gnoise1 + rt1*gnoise2)
      return
      end      

C*********************************************************************
