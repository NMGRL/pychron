C	CHTEST.F   CALCULATION OF CHEBYSHEV COEFFICIENT AND APPROX.
     
      implicit double precision (a-h,o-z)	
      parameter(ns=200,nc=100,ntst=1001,mxi=350,nn=319,mfit=10,nwcy=10,
     $nd=10,xlambd=0.0005543d00,a=0.d00,perc=0.01d00,cht0=1.d-4)
      dimension c(nc),tt(2,0:ntst),d0(nd),r39(0:ns),xi(0:2*nc,nd,mxi)
      dimension xmat(nd,0:ns,mxi),lc(mxi),vc(nd),tilab(ns),telab(ns)
      dimension ys(0:ns),wt(ns),lista(nc),covar(nc,nc),alpha(nc,nc) 
      dimension dyda(nc),chq(nwcy),c0(nc)
      common /cont/ ncyc,nmaxi(nwcy),nmaxo(nwcy)
      common /var/ tti(nwcy,2,ntst),tto(nwcy,2,ntst),
     $agei(nwcy,2,ns),ageo(nwcy,2,ns)
      double precision slope
      external slope
      character*9  tab1
      tab1=char(09)
      nn1=nn

C	OUTPUT FILES

      open(unit=20,file='param-mon.out')
      open(unit=21,file='mages-sd.samp')
      open(unit=32,file='mchisq.dat')
      open(unit=40,file='mchistall-inp.dat')
      open(unit=42,file='mchistall-out.dat')
      open(unit=44,file='magesall-inp.dat')
      open(unit=46,file='magesall-out.dat')

C	INPUT FILES
      open(unit=22,file='age.in',status='old')
      open(unit=24,file='sig.in',status='old')
      open(unit=30,file='arr-me.in',status='old')          	
      open(unit=17,file='temstep.in',status='old')

	  open(unit=51,file='autoagemon.cl',status='old')


C     INITIALIZATION OF OUTPUT FILES FOR XVGR SETS
      kc0=48
      kc1=48
      mcyc= 0
      call wgraph(40,kc1)
      call wgraph(42,kc1)
      call wgraph(44,kc1)
      call wgraph(46,kc1)

	
C      print *, 'Insert Number of runnings'
	read (51,*) nrun
C       print *, 'Insert max. plateau age'
      read (51,*) tt(1,1)

        agein=tt(1,1)     
	idem= -tt(1,1)*nrun
        np= 3
       tt(2,1)= 500.d00
       tt(2,2)=300.d00
       tt(1,2)=tt(1,1)/2.d0
       tt(2,3)=0.d00
       tt(1,3)= 0.d0
	ncyc=1
        chqmin=1.0d20
        read(17,*)ni
        do 12 j=1,ni
            r39(j)=0.d0
            read(17,*)telab(j),tilab(j)
	    if(telab(j).gt.1373.)goto 11
12      tilab(j)=tilab(j)/5.256d11
11      ni=j-1
         close(17)

       read(30,*)nst
       do 14 js=1,nst
            read(30,*)e,d0(js),vc(js)
            d0(js)= 10.d0**d0(js)
14     d0(js)=d0(js)/4.d0 *(24.d0 *3600.d0 *365d06)
       close(30)
C     CALCULATION OF LC
	  nchini=0
      nsq=2
      nsum=0
      m=-1
      do 32 mi=1,nn
        if(nsum.gt.20)then
          nsum=1
          nsq=2*nsq
        endif
        m=m+nsq
        if(m.gt.200)nsum=nsum+1
           lc(mi)=m
32    continue
       call lab(r39,d0,e,vc,telab,tilab,lc,xmat,ni,nst,nn)
       call agesamp(r39,ys,wt,ni)

      call chebft(a,tt(1,1),c,nc,slope,tt,np)
       do 13 i=1,mfit
             lista(i)=i
             c0(i)=c(i)
13       continue
34     call ranchist(c,c0,mfit,idem,tt(2,1))
       dch=0d00
        alamda=-1
           call mrqmin(r39,ys,wt,ni,c,nc,lista,mfit,covar,alpha,
     $      nc,chisq,alamda,tt,xmat,lc,vc,d0,E,nst,nn1)
          k=1
          itst=0
          write(20,*)'  chi-squared:  ',ni*chisq
        alam=alamda
1       write(20,*)'it #=',k,'   alamda:',alamda
        if(dch.gt.0.d0)then
          write(20,*)
          write(20,*)'  chi-squared:  ',ni*chisq
        endif
            k=k+1
            ochisq=chisq
           call mrqmin(r39,ys,wt,ni,c,nc,lista,mfit,covar,alpha,
     $      nc,chisq,alamda,tt,xmat,lc,vc,d0,E,nst,nn1)
            dch=abs(ochisq-chisq)
            cht=cht0*chisq
            if (dch.lt.cht.and.alamda.lt.alam) then
               itst=itst+1
               write(20,*)'itst= ',itst
            endif
            alam=alamda
           if (itst.lt.3.) then
               goto 1
           endif
           write(20,*)'difference= ',(ochisq-chisq)*ni
           chq(ncyc)=chisq
           aq= 0.5d0 * (ni-2.d0)
           q= gammq(aq,0.5*ni*chisq)
           write(20,*)'chisq= ',ni*chisq,'  GOF= ',q
           alamda=0.d0
	  c40=1.d0-dexp(-xlambd*tt(1,1))
         call zita(c,nc,lista,mfit,lc,xi,tt(1,1),d0,E,tt,nst
     $   ,nn,perc,alamda)
     
C         write(20,'(1x,t5,a,t12,a,t19,a,t26,a,t33,a,t40,a,t47,a,t54,
c     $    a,t61,a,t68,a)')'c(1)','c(2)','c(3)' 
C     $	 ,'c(4)','c(5)','c(6)','c(7)','c(8)','c(9)','c(10)'
C           write(20,'(1x,10f7.3)') (c(i),i=1,10)
         do 42 i=1,ni
             call age(i,c,ymod,dyda,nc,lista,mfit,vc,xmat,r39,xi,
     $       c40,nn,nst,ni,perc,alamda)
 42    continue
          print *, nchini
          write(32,*) nchini,chisq
	if (nchini.eq.0)chqmin= chisq

            nchini= nchini + 1
	    write(20,*)
            write(20,*) 'New cycle:',nchini
            write(20,*)

	    if (ncyc.eq.nwcy.or.nchini.eq.nrun)then
               open(unit=10,file='mchist-inp.dat')
               open(unit=12,file='mchist-out.dat')
               open(unit=18,file='mages-inp.dat')
               open(unit=19,file='mages-out.dat')
               open(unit=48,file='status.info')
               if(nchini.gt.nwcy)then
                 call readfile(10)
		 call readfile(12)
		 call readfile(18)
		 call readfile(19)
                 call readfile(48)
               else
      		 call wgraph(10,kc0)
      		 call wgraph(12,kc0)
      		 call wgraph(18,kc0)
      		 call wgraph(19,kc0)
                 write(48,*)'program initialization'
               endif
              if(ncyc.eq.nchini)then
                do 300 j=1,ncyc
                   if(chq(j).lt.chqmin)chqmin= chq(j)
300	        continue
              endif

              do 310 j=1,ncyc
                  kcyc= nchini-ncyc+j
C   WRITE OF ALL SETS 
	          do 362 j1=1,ni
		    write(44,100)agei(j,1,j1),tab1,agei(j,2,j1)
                    write(44,100)agei(j,1,j1+1),tab1,agei(j,2,j1)
		    write(46,100)ageo(j,1,j1),tab1,ageo(j,2,j1)
		    write(46,100)ageo(j,1,j1+1),tab1,ageo(j,2,j1)
362               continue
                do 322 j1=1,nmaxi(j)
                    write(40,100)tti(j,1,j1),tab1,tti(j,2,j1)
322               continue
	          do 342 j1=1,nmaxo(j)
                    write(42,100)tto(j,1,j1),tab1,tto(j,2,j1)
342               continue
                  if(kcyc.ne.nrun)then
                    write(40,*)'&  cycle #',kcyc
                    write(42,*)'&  cycle #',kcyc,' chisq= ',chq(j)*ni
                    write(44,*)'&  cycle #',kcyc
                    write(46,*)'&  cycle #',kcyc
                  endif                  
                  if(kcyc/30*30-kcyc.eq.0.and.kcyc.ne.nrun)then
                    kc1=kc1+1
                    call wgraph(40,kc1)
                    call wgraph(42,kc1)
                    call wgraph(44,kc1)
                    call wgraph(46,kc1)
                  endif

C   WRITE OF SELECTED SETS 
                if(chq(j).lt.chqmin*1.5d0)then
                  mcyc=mcyc+1
                  do 320 j1=1,nmaxi(j)
                    write(10,100)tti(j,1,j1),tab1,tti(j,2,j1)
320               continue
                  n1=0
	          do 340 j1=1,nmaxo(j)
                    write(12,100)tto(j,1,j1),tab1,tto(j,2,j1)
                    if(tto(j,2,j1).lt.100.and.tto(j,1,j1-1).lt.agein
     $                .and.n1.eq.0)then
                      agein=tto(j,1,j1-1)
                      n1=1
                   endif
340		  continue
                 write(48,*)'total runs done= ',kcyc,' 
     $          sucessful runs= ',mcyc
	          do 360 j1=1,ni
		    write(18,100)agei(j,1,j1),tab1,agei(j,2,j1)
                    write(18,100)agei(j,1,j1+1),tab1,agei(j,2,j1)
		    write(19,100)ageo(j,1,j1),tab1,ageo(j,2,j1)
		    write(19,100)ageo(j,1,j1+1),tab1,ageo(j,2,j1)
360               continue
                  write(10,*)'&  cycle #',kcyc
                  write(12,*)'&  cycle #',kcyc,' chisq= ',chq(j)*ni
                  write(18,*)'&  cycle #',kcyc
                  write(19,*)'&  cycle #',kcyc
                  if(mcyc/30*30-mcyc.eq.0.and.kcyc.ne.nrun)then
                    kc0=kc0+1
                    call wgraph(10,kc0)
                    call wgraph(12,kc0)
                    call wgraph(18,kc0)
                    call wgraph(19,kc0)
                  endif
                endif	       
310            continue
  	        ncyc=1
                close(10)
                close(12)
                close(18)
                close(19)
                close(48) 
	    else 
                ncyc=ncyc + 1
            endif 
                  
            if(nchini.ne.nrun)goto 34

C     REMOVE LAST '&' FROM OUTPUT FILES ???

      write(20,*)'End of CH cycles, total= ',nrun,'  completed=',mcyc
      close(12)
      close(22)
      close(24)
      close(30)
      call conf_int(agein,tt(1,1))
      stop 'End of CH cycles'
140   format(1x,4(f12.4,a1))
120   format(1x,f5.2,6(f12.4))
100   format(1x,6(g20.8,a1))

      end


C   SUBROUTINE RANCHIST

      subroutine ranchist(c,c0,mc,idem,tini)
      implicit double precision (a-h,o-z)
      dimension c(mc), c0(mc) 
           fsum2= 0.d0      
           do 30 l=1,mc
              perc= 5.d0 * ran1(idem)*(0.6 - ran1(idem))
              c(l)=c0(l) + perc
30	   continue
20	continue
        tini= (0.5-ran1(idem))*200 + 400
        return
       end          

C   FUNCTION RAN1

      double precision function ran1(idum)
      implicit double precision (a-h,o-z)
        save ix1,ix2,ix3,r
      dimension r(97)
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
           write(20,*)'ERROR(RAN1): (j.gt.97.or.j.lt.1)'
           stop 'ERROR(RAN1): (j.gt.97.or.j.lt.1)'
      endif
      ran1=r(j)
      r(j)=(float(ix1)+float(ix2)*rm2)*rm1
      return
      end

C   SUBROUTINE AGESAMP

      subroutine agesamp(r39,ys,wt,ni)
      implicit double precision (a-h,o-z)
      parameter (ns=200)
      dimension xs(0:ns),ys(0:ni),r39(0:ni+1),ya(0:ns)
      dimension wt(ni+1),sig(ns)
           j=1
 1         read(24,*,END=10)sig(j)
           if(sig(j).le.0.)then
            write(20,*)'ERROR(AGESAMP): (sig(j).le.0)'
	    stop 'ERROR(AGESAMP): (sig(j).le.0)'
           endif
           read(22,*,END=10)xs(j),ya(j)
	   write(21,100)xs(j-1)*100.d0,ya(j)+sig(j)
	   write(21,100)xs(j),ya(j)+sig(j)
           xs(j)=xs(j)/100.d00
           wt(j)=1.d00/dsqrt(dabs(r39(j)-r39(j-1)))*sig(j)
           j=j+1
           goto 1
10      continue
	do 90 k=1,j-1
	write(21,100)xs(j-k)*100.,ya(j-k)-sig(j-k)
	write(21,100)xs(j-k-1)*100.,ya(j-k)-sig(j-k)
   90	continue
        write(21,100)xs(0),ya(1)+sig(1)

C EXTRAPOLATION FROM NI FOR FITTING CALCULATION

        ya(0)=ya(1)
      xs(ni+1)=1.d00
      ys(ni+1)=ys(ni)
      jold= 1
      do 30 k=1,ni
        ys(k)=0.d0
        do 20 j=jold,ni+1
         if(xs(j-1).lt.r39(k).and.xs(j).gt.r39(k))then
            if(jold.eq.j)then
              ys(k)=ya(j)
            else
              do 34 jm=jold+1,j-1
                ys(k)=ya(jm)*(xs(jm)-xs(jm-1))+ys(k)
34	      continue
        ys(k)=ys(k)+ya(jold)*(xs(jold)-r39(k-1))+ya(j)*(r39(k)-xs(j-1))
              ys(k)=ys(k)/(r39(k)-r39(k-1))
              jold=j
            endif
            goto 30
         endif
20      continue         
30      continue
         return
100   format(1x,4(f14.8))
         end

C    SUBROUTINE LAB

      subroutine lab(r39,d0,e,vc,telab,tilab,lc,xmat,ni,nst,nn)
      implicit double precision (a-h,o-z)
      parameter(pi=3.14159265359d00,imp=2,
     $b=8.d0,ns=200,R= 1.987d-03,nd=10)
      dimension xmat(1:nd,0:ns,1:nn),lc(nn),zita(0:ns),r39(0:ni)
      dimension tilab(ni),telab(ni),d0(nst),vc(nst)
C      character*9  tab1
C      tab1=char(09)
      zita(0)=0.d00   
         nsq=2
         nsq1=1
         do  60 j=1,nn
             an2=(lc(j)*pi)**2
             xmat(1,ni+1,j)=b/an2
           if(j.ge.121)then
              if((j-121)/20*20-(j-121).eq.0)then
                 nsq=nsq*2
                 nsq2=nsq/imp
              endif
              do 64 mi=1,nsq1-1
                   an=((lc(j)-mi*imp)*pi)**2
                   xmat(1,ni+1,j)=xmat(1,ni+1,j)+b/an*(nsq1-mi)/nsq1
64         continue
	if(j.eq.nn)goto 60
             do 68 mi=1,nsq2-1
                   an=((lc(j)+mi*imp)*pi)**2
                   xmat(1,ni+1,j)=xmat(1,ni+1,j)+b/an*(nsq2-mi)/nsq2
68         continue
              nsq1=nsq2
          endif
60      continue
      do 10 k=1,nst   
      do 10 nt=1,ni
              if(k.eq.1)r39(nt)=0.d0
          zita(nt)=zita(nt-1)+d0(k)*tilab(nt)*dexp(-e/(r*telab(nt)))
         nsq=2
         nsq1=1
         do 48 j=1,nn
            an2=(lc(j)*pi)**2
                    if(an2*zita(nt).gt.60)then
                          do 70 jx=j,nn
                               xmat(k,nt,jx)=xmat(1,ni+1,jx)
70                      continue
                          goto 72
                    else
               xmat(k,nt,j)=xmat(1,ni+1,j)-b*dexp(-an2*zita(nt))/an2
                    endif
            if(j.ge.121)then
              if((j-121)/20*20-(j-121).eq.0)then
                 nsq=nsq*2
                 nsq2=nsq/imp
              endif
              do 42 mi=1,nsq1-1
                an=((lc(j)-mi*imp)*pi)**2
                   xmat(k,nt,j)=xmat(k,nt,j)-b*dexp(-an*zita(nt))
     $                /an* (nsq1-mi)/nsq1                  
42         continue
	if(j.eq.nn)goto 50
            do 44 mi=1,nsq2-1
                an=((lc(j)+mi*imp)*pi)**2
                 xmat(k,nt,j)=xmat(k,nt,j)-b*dexp(-an*zita(nt))
     $                /an*(nsq2-mi)/nsq2                  
44          continue
            nsq1=nsq2
          endif
50           continue
48      continue
72             do 20 k1=1,80000,imp
                 an2=(k1*pi)**2
                 r39(nt)=r39(nt)+b/an2*vc(k)
                if (zita(nt)*(k1*pi)**2.gt.100.) then
                    ab= 0.d00
               else
                    ab= dexp(-zita(nt)*(k1*pi)**2)/(k1*pi)**2
                    r39(nt)=r39(nt)-b*ab*vc(k)
               endif
20       continue
10    continue
         return
         end

C   SUBROUTINE CHEBFT

      subroutine chebft(a,b,c,n,func,tt,np)
      implicit double precision (a-h,o-z)
      parameter (nmax=100, pi=3.141592653589793d0)
      dimension c(n),f(nmax),tt(2,0:np)
      bma=0.5d00*(b-a)
      bpa=0.5d00*(b+a)
      do 11 k=1,n
        y=dcos(pi*(k-0.5d0)/n)
        f(k)=func(tt,np,y*bma+bpa)
11    continue
      fac=2.d0/n
      do 13 j=1,n
        sum=0.d0
        do 12 k=1,n
          sum=sum+f(k)*dcos((pi*(j-1))*((k-0.5d0)/n))
12      continue
        c(j)=fac*sum
13    continue
      return
      end

C    DOUBLE PRECISION FUNCTION SLOPE

      double precision function slope(a,n,x)
      implicit double precision (a-h,o-z)
      dimension a(2,0:n)
      do 10 j=2,n
        if(a(1,j).lt.x.and.a(1,j-1).gt.x)then
          slope=dsqrt(dabs((a(2,j-1)-a(2,j))/(a(1,j-1)-a(1,j))))
          return
       endif
10    continue
      end

C    SUBROUTINE MRQMIN

      subroutine mrqmin(x,y,sig,ndata,a,ma,lista,mfit,
     *    covar,alpha,nca,chisq,alamda,tt,xmat,
     *    lc,vc,d0,E,nst,nn)
      implicit double precision (a-h,o-z)
      parameter (mmax=100,ntst=1001,nd=10,ns=200)
      dimension x(0:ndata),y(0:ndata),sig(ndata),a(ma),lista(ma),
     * covar(nca,nca),alpha(nca,nca),atry(mmax),beta(mmax),da(mmax),
     * xmat(1:nd,0:ns,1:nn),d0(nst),vc(nst),tt(2,0:ntst),lc(nn)
     * ,covaux(mmax,mmax),daux(mmax)
        save beta,atry,da,ochisq
      if(alamda.lt.0.)then
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
            write(20,*)'ERROR(MRQMIN): improper permutation in lista-1'
            stop 'ERROR(MRQMIN): improper permutation in lista-1'
          endif
12      continue
        if (kk.ne.(ma+1))then
          write(20,*)'ERROR(MRQMIN): improper perm. in lista-2'
          stop 'ERROR(MRQMIN): improper perm. in lista-2'
        endif
        call mrqcof(x,y,sig,ndata,a,ma,lista,mfit,alpha,beta,nca,chisq,
     *tt,xmat,lc,vc,d0,e,nst,nn,alamda)
        alamda=0.001d0
        ochisq=chisq
        do 13 j=1,ma
          atry(j)=a(j)
13      continue
      endif
      do 15 j=1,mfit
        do 14 k=1,mfit
          covar(j,k)=alpha(j,k)
14      continue
        covar(j,j)=alpha(j,j)*(1.d0+alamda)
        da(j)=beta(j)
15    continue
      ng= 1
      call gaussj(covar,mfit,nca,da,ng,1)
      if(ng.eq.-1)stop 'Singular Matrix'
      if(alamda.eq.0.)then
        call covsrt(covar,nca,ma,lista,mfit)
        return
      endif
      do 16 j=1,mfit
        if(alamda.ge.1.00d20)then
           da(j)=0.d0
        endif
        atry(lista(j))=a(lista(j))+da(j)
16    continue
      call mrqcof(x,y,sig,ndata,atry,ma,lista,mfit,covar,da,nca,chisq,
     *tt,xmat,lc,vc,d0,e,nst,nn,alamda)
      if(chisq.le.ochisq)then

C  CHECK IF COVAR IS NOT SINGULAR         
        do 19 j=1,mfit
          do 20 k=1,mfit
            covaux(j,k)=covar(j,k)
20        continue
          daux(j)=da(j)
19       continue
         call gaussj(covaux,mfit,nca,daux,ng,1)
         if(ng.eq.-1)then
             alamda=10.d0*alamda
             chisq=ochisq
	     ng= 1
             return
         endif
C   END CHECKING FOR SINGULAR MATRIX
 
        alamda=0.1d0*alamda
        ochisq=chisq
        do 18 j=1,mfit
          do 17 k=1,mfit
            alpha(j,k)=covar(j,k)
17        continue
          beta(j)=da(j)
          a(lista(j))=atry(lista(j))
18      continue
      else
        alamda=10.d0*alamda
        chisq=ochisq
      endif
      return
      end

C     SUBROUTINE MRQCOF

      subroutine mrqcof(x,y,sig,ndata,a,ma,lista,mfit,alpha,beta,nalp,
     *chisq,tt,xmat,lc,vc,d0,e,nst,nn,al)
      implicit double precision (a-h,o-z)
      parameter (mmax=100,ntst=1001,perc=0.01d0,xlambd=0.0005543d0,
     *nc=100,mxi=500,nd=10,ns=200)
      dimension x(0:ndata),y(0:ndata),sig(ndata),alpha(nalp,nalp),
     * dyda(mmax),lista(mfit),a(ma),xmat(1:nd,0:ns,1:nn),d0(nst),
     * vc(nst),tt(2,0:ntst),lc(nn),beta(ma),xi(0:2*nc,nd,mxi)
      t0=tt(1,1)
      c40=1.d0-dexp(-xlambd*t0)
      do 12 j=1,mfit
        do 11 k=1,j
          alpha(j,k)=0.d0
11      continue
        beta(j)=0.d0
12    continue
       call zita(a,ma,lista,mfit,lc,xi,t0,d0,E,tt,nst,nn,perc,al)
      if(tt(2,ntst).eq.-1.)then
         tt(2,ntst)=0.d0
         chisq=chisq*2.d0
         return
      endif
      chisq=0.d0
      do 15 i=1,ndata
        call age(i,a,ymod,dyda,ma,lista,mfit,vc,xmat,x,xi,c40,nn,
     * nst,ndata,perc,al)
        sig2i=1.d0/(sig(i)*sig(i))
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

C   SUBROUTINE COVSRT

      subroutine covsrt(covar,ncvm,ma,lista,mfit)
      implicit double precision (a-h,o-z)
      dimension covar(ncvm,ncvm),lista(mfit)
      do 12 j=1,ma-1
        do 11 i=j+1,ma
          covar(i,j)=0.d0
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
        covar(j,j)=0.d0
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

C   SUBROUTINE GAUSSJ

      subroutine gaussj(a,n,np,b,m,mp)
      implicit double precision (a-h,o-z)
      parameter (nmax=100)
      dimension a(np,np),b(np,mp),ipiv(nmax),indxr(nmax),indxc(nmax)
      do 11 j=1,n
        ipiv(j)=0
11    continue
      do 22 i=1,n
        big=0.d0
        do 13 j=1,n
          if(ipiv(j).ne.1)then
            do 12 k=1,n
              if (ipiv(k).eq.0) then
                if (dabs(a(j,k)).ge.big)then
                  big=dabs(a(j,k))
                  irow=j
                  icol=k
                endif
              else if (ipiv(k).gt.1) then
                write(20,*)'ERROR(GAUSS): singular matrix-1'
                m=-1
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
          write(20,*)'ERROR(GAUSS): singular matrix-2'
           m=-1
           return
        endif
        pivinv=1.d0/a(icol,icol)
        a(icol,icol)=1.d0
        do 16 l=1,n
          a(icol,l)=a(icol,l)*pivinv
16      continue
        do 17 l=1,m
          b(icol,l)=b(icol,l)*pivinv
17      continue
        do 21 ll=1,n
          if(ll.ne.icol)then
            dum=a(ll,icol)
            a(ll,icol)=0.d0
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

C   SUBROUTINE ZITA

       subroutine zita(c,mc,lista,mfit,lc,xi,t0,d0,E,tt,nst,
     $  nn,perc,al)
        implicit double precision (a-h,o-z)
        parameter(ntst=1001,a=0,nc=100,nwcy=10,ns=200)
      dimension lc(nn),d0(nst),lista(mfit)
      dimension c(mc),tt(2,0:ntst),xi(0:2*nc,1:nst,1:nn)
      common /var/ tti(nwcy,2,ntst),tto(nwcy,2,ntst),
     $agei(nwcy,2,ns),ageo(nwcy,2,ns)
      common /cont/ ncyc,nmaxi(nwcy),nmaxo(nwcy)
      character*9  tab1
      tab1=char(09)
      n=0
      call sched(a,t0,c,mc,tt,imax)
      call geosec(imax,d0,E,tt,xi,nn,lc,nst,n)
      write(20,*)'# of CH points= ',imax
      if(al.le.0.)then
         if (al.lt.0) then
            nmaxi(ncyc)=imax
         else
            nmaxo(ncyc)=imax
         endif
        do 40 j=1,imax
           if (al.lt.0) then
	       tti(ncyc,1,j)=tt(1,j)
               tti(ncyc,2,j)=tt(2,j)
           else 
	       tto(ncyc,1,j)=tt(1,j)
               tto(ncyc,2,j)=tt(2,j)
           endif
40      continue
      endif
      do 20 k=1,mfit
         csk=c(lista(k))
         dc=perc * dabs(c(lista(k)))
         do 30 js=1,2
            n=n+1
            c(lista(k))=c(lista(k))+(-1)**js*dc
            call sched2(a,t0,c,mc,tt,imax)
            call geosec(imax,d0,E,tt,xi,nn,lc,nst,n)
            c(lista(k))=csk
30        continue
20    continue

100   format(1x,6(g20.8,a1))
       return
       end

C    SUBROUTINE AGE

       subroutine age(nt,c,y,dyda,mc,lista,mfit,vc,xmat,r39,xi,c40,
     *nn,nst,ndata,perc,al)
      implicit double precision (a-h,o-z)
      parameter(xlambd=0.0005543d0,nc=100,nd=10,ns=200,nwcy=10,
     $ntst=1001)
      dimension xmat(1:nd,0:ns,1:nn),r39(0:ndata),lista(mfit)
      dimension c(mc),dyda(mc),vc(nst),xi(0:2*nc,1:nst,1:nn)
      common /var/ tti(nwcy,2,ntst),tto(nwcy,2,ntst),
     $agei(nwcy,2,ns),ageo(nwcy,2,ns)
      common /cont/ ncyc,nmaxi(nwcy),nmaxo(nwcy)
      character*9  tab1
      tab1=char(09)
        c39wd=1.d0 - c40
        s1=0.d0
      do 52 k=1,nst
      do 52 m=1,nn
         s1=s1 + vc(k)*xi(0,k,m)*(xmat(k,nt,m)-xmat(k,nt-1,m))
52    continue
      dr39=r39(nt)-r39(nt-1)
      dr40=dr39*(c40-1)+s1
      y=0.d0
      if(dr40/dr39.gt.0.)then
         y=dlog(1.d0+dr40/dr39/c39wd)/xlambd
         dya=1.d0/(dr39*c39wd+dr40)/xlambd
      endif
      if(al.lt.0)then
        agei(ncyc,1,nt+1)=r39(nt)*100.d0
	agei(ncyc,2,nt)=y
      else if (al.eq.0.) then
        ageo(ncyc,1,nt+1)=r39(nt)*100.d0
	ageo(ncyc,2,nt)=y
      endif
42    continue
      do 56 ls=1,mfit
         l=ls*2-1
         dc=perc*dabs(c(lista(ls)))
         s1=0.d0
         do 54 k=1,nst
         do 54 m=1,nn
             dxi=  (xi(l+1,k,m)-xi(l,k,m))/(2*dc)
             s1=s1 + vc(k)*(xmat(k,nt,m)-xmat(k,nt-1,m))*dxi
54    continue
         dyda(lista(ls))=s1*dya
56    continue 
100   format(1x,4(g20.8,a1))
      return
      end

C     SUBROUTINE GEOSEC

      subroutine geosec(imax,d0,E,tt,xi,nn,lc,nst,j1)
      implicit double precision (a-h,o-z)
      parameter(xlambd=5.543d-04,R=1.987d-03,max=1002,
     $pi=3.14159265359d0,nc=100)
       dimension xi(0:2*nc,1:nst,1:nn),tt(2,0:imax),dzita(0:max)
      dimension lc(nn),d0(nst),d(0:max)
C      character*9   tab1
C      tab1=char(09)
C      nn=319
      do 80 k=1,nst
      nend=imax-1
      do 10 j=1,nend
        avtemp=(tt(2,j+1)+tt(2,j))/2.d0 + 273.d0
        if(e/r/avtemp.gt.80)then
            d(j)=0.d0
            goto 10
        endif
        d(j)=d0(k)*dexp(-e/r/avtemp)
10    continue
60    dzita(nend+1)=0.d0
      do 20 j=nend,1,-1
20    dzita(j)=dzita(j+1)+dabs(tt(1,j+1)-
     $tt(1,j))*d(j)
C     COMPUTO OF XI(M) - M<80000 --> nn=319
      do 30 mi=1,nn
        xlogm=2*dlog(lc(mi)*pi)
        sum=0.d0
          do 40 n=1,nend
            if(d(n).eq.0.)goto 40
            uplus=(lc(mi)*pi)**2*dzita(n+1)+xlambd*(tt(1,1)-tt(1,n+1))
            if (uplus-xlogm.gt.25.)goto 40
              al=(lc(mi)*pi)**2*d(n)-xlambd
              xal= al *(tt(1,n)-tt(1,n+1))
              if (dabs(xal).gt.30)then
                    camal=1.d0/al
              else
                    if (dabs(xal).gt.0.001)then
                        camal=(1.d0-dexp(-xal))/al
                   else
                       camal=(tt(1,n)-tt(1,n+1))*(1-xal/2+xal**2/6.d0)
                   endif
              endif
            sum=sum+d(n)*dexp(-uplus)*camal
40        continue
          tzita= dzita(1)*(pi*lc(mi))**2
          if(tzita.lt.30.)then
               xfact= dexp(-tzita)
          else
               xfact= 0.
          endif
          xi(j1,k,mi)=sum*(pi*lc(mi))**2 + xfact
30    continue
80    continue
      return
      end

C      SUBROUTINE SCHED

      subroutine sched(a,t0,c,m,tt,i)
       implicit double precision (a-h,o-z)
      parameter(step=4.d0,nt=10000,ntst=1001,tmax=100.d0)
      dimension tt(2,0:ntst),c(m)
	i=1
        slp=(chebev(a,t0,c,m,t0))**2
	dt=t0/nt
        sum=slp*dt/2.d0
        do 10 j=1,nt
           xj=t0-j*dt
           if(j.eq.nt)xj=0.d0
          slp=(chebev(a,t0,c,m,xj))**2
           sum= sum + slp * dt/2
  	   if(sum.ge.step.or.xj.eq.0.)then
             tt(2,i+1)=tt(2,i)-sum
	     tt(1,i+1)=xj
             sum= 0.d0
             i=i+1
             if(tt(2,i).le.tmax)goto 20
           endif
           sum= sum + slp * dt/2
10	continue
        return
20      tt(2,i)=0.d0
        tt(1,i)=0.d0
        return
        end

       subroutine sched2(a,t0,c,m,tt,i)
       implicit double precision (a-h,o-z)
      parameter(nt=10000,ntst=1001,tmax=100.d0)
      dimension tt(2,0:ntst),c(m)
	i=1
        slp=(chebev(a,t0,c,m,t0))**2
	dt=t0/nt
        sum=slp*dt/2.d0
        do 10 j=1,nt
           xj=t0-j*dt
           if(j.eq.nt)xj=0.d0
           slp=(chebev(a,t0,c,m,xj))**2
           sum= sum + slp * dt/2
  	   if(xj.eq.tt(1,i+1))then
             tt(2,i+1)=tt(2,i)-sum
             sum= 0.d0
             i=i+1
             if(tt(2,i).le.tmax)goto 20
           endif
           sum= sum + slp * dt/2
10	continue
        return
20      tt(2,i)=0.d0
        tt(1,i)=0.d0
        return
        end


C     SUBROUTINE CHEBEV

      function chebev(a,b,c,m,x)
      implicit double precision (a-h,o-z)
      dimension c(m)
      if ((x-a)*(x-b).gt.0.) then
	 write(20,*)'ERROR(CHEBEV): x not in range'
         stop 'ERROR(CHEBEV): x not in range'
      endif
      d=0.d0
      dd=0.d0
      y=(2.d0*x-a-b)/(b-a)
      y2=2.d0*y
      do 11 j=m,2,-1
        sv=d
        d=y2*d-dd+c(j)
        dd=sv
11    continue
      chebev=y*d-dd+0.5d0*c(1)
      return
      end 


      double precision function gammq(a,x)
      implicit double precision (a-h,o-z)
      if(x.lt.0..or.a.le.0.)then
        write(20,*)'ERROR(GAMMQ): (x.lt.0..or.a.le.0.)'
        stop 'ERROR(GAMMQ): (x.lt.0..or.a.le.0.)'
      endif
      if(x.lt.a+1.)then
        call gser(gamser,a,x,gln)
        gammq=1.-gamser
      else

        call gcf(gammcf,a,x,gln)
        gammq=gammcf
      endif
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
          if(dabs((g-gold)/g).lt.eps)go to 1
          gold=g
        endif
11    continue
      write(20,*)'ERROR(GCF): a too large, itmax too small'
      stop 'ERROR(GCF): a too large, itmax too small'
1     gammcf=dexp(-x+a*dlog(x)-gln)*g
      return
      end

      subroutine gser(gamser,a,x,gln)
      implicit double precision (a-h,o-z)
      parameter (itmax=100,eps=3.e-7)
      gln=gammln(a)
      if(x.le.0.)then
        if(x.lt.0.)then
	  write(20,*)'ERROR(GSER): (x.lt.0.)'
          stop 'ERROR(GSER): (x.lt.0.)'
        endif
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
        if(dabs(del).lt.dabs(sum)*eps)go to 1
11    continue
      write(20,*)'ERROR(GSER): a too large, itmax too small'
      stop 'ERROR(GSER): a too large, itmax too small'
1     gamser=sum*dexp(-x+a*dlog(x)-gln)
      return
      end

C   SUBROUTINE WGRAPH
      subroutine wgraph(n,k)
        character *2,graph
        if(k.lt.48.or.k.gt.57)return
        graph= 'g'//char(k)
        write(n,120)'@WITH '//graph
        write(n,130)'@'//graph//' ON'
120	format(a8)
130	format(a6)
        return
        end


        subroutine readfile(l)
10      read(l,*,end=20)
        goto 10
20      return
        end




C  CONF_INT.F  CALCULATES THE INTERVAL OF CONFIDENCE FROM 
C  A SET OF THERMAL HISTORIES. 
      subroutine conf_int(agein,agend)   
      implicit double precision (a-h,o-z)	
      parameter(ns=200,cn=12,R=1.987D-3,dt=20.d0,tau1=3.,tau2=1)
      parameter(tim=3.15576d13,pi=3.14159265,nt=1000)
      dimension temp(nt,ns),time(nt,ns),xtem(ns),nch(ns)
      dimension xmed(ns),ave(ns),adev(ns),sdev(ns),xmed2(ns),
     $  var(ns),skew(ns),curt(ns),xage(ns),xmed1(ns)
      external temfc
      open(unit=22,file='mchist-out.dat',status='old')        
C      open(unit=24,file='statanal.dat')
C      open(unit=26,file='average.dat')
C      open(unit=28,file='confint.dat')
      open(unit=29,file='confmed.dat')
C      open(unit=30,file='input.dat')
      ncyc= 0
      ncurv= 0
      nsteps= 100
      dage= (agend - agein)/nsteps
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
      goto 1
13    ks=ks-1
          if(ks.lt.20)then
            write(29,*)'Not enough solutions to calculate 
     $       confidence intervals'
            return
          endif
C  CALCULATES THE XTEM VECTOR FOR EACH TIME     
	do 10 j=1,nsteps+1
	    xage(j)= agein + (j-1)*dage
	    xmed(j)= 0
	    do 22 k=1,ks
	    	if (xage(j).gt.time(1,k))goto 10
            xtem(k)= temfc(time(1,k),temp(1,k),nch(k),xage(j))
22	    continue
C	    STATISTICAL CALCULATIONS
C	    MEAN OF THE DISTRIBUTION	    
	    call moment(xtem,ks,ave(j),adev(j),sdev(j),
     $     var(j),skew(j),curt(j))
          call mdian1(xtem,ks,xmed(j))          
          nperc= ks*.05
          call binom(ks+1,j1,j2)
          if(j.eq.1)then
               xmed0=xtem(j2)
               xmed02=xtem(ks-nperc)
          endif
          xmed1(j)=xtem(j1)
          xmed2(j)=xtem(nperc)
C  WRITE INTERVAL OF CONFIDENCE OF MEDIAN and DISTRIBUTION
C          write(24,110)xage(j),ave(j),xmed(j),sdev(j),adev(j),
C     $      var(j),skew(j),curt(j)
C          write(26,110)xage(j),ave(j),xmed(j),xmed(j)+sdev(j),
C     $      xmed(j)-sdev(j)
C          write(28,110)xage(j),xtem(j2),xmed(j)+sdev(j),
C     $      xmed(j)+2.*sdev(j)
          write(29,110)xage(j),xtem(ks-nperc),xtem(j2)    
10	continue 
      do 12 j=nsteps+1,1,-1
C          write(28,110)xage(j),xmed1(j),xmed(j)-sdev(j),
C     $      xmed(j)-2.*sdev(j)
          write(29,110)xage(j),xmed2(j),xmed1(j)    
12	continue 
C          write(28,110)xage(1),xmed0,xmed(1)+sdev(1),
C     $      xmed(1)+2.*sdev(1)      
          write(29,110)xage(1),xmed02,xmed0
C  WRITE INTERVAL OF CONFIDENCE
14        return 
100	format(100(I5,1x))
110   format(8f8.2)
	end

C FUNCTION TEMFC (CALCULATES THE TEMPERATURE AT ANY GIVEN AGE)
      double precision function temfc(time,temp,ni,x)
      implicit double precision (a-h,o-z)
      dimension time(ni),temp(ni)
      temfc= 0.d0
      if(x.eq.time(1))then
         temfc=temp(1)
         return
      endif
      do 10 j=ni-1,1,-1
        if(time(j).gt.x.and.time(j+1).le.x)then
          slope=  (temp(j+1)-temp(j))/(time(j+1)-time(j))
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
        skew= 0.
        curt= 0.
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
            f= bico(n,k)*0.5**n + f
12       continue
         if(f.le.0.05)then
            if(dabs(faux-.05).lt.dabs(f-.05))j1=j1+1
	    goto 14
          endif
10    continue
14    do 20 j=nmed+1,n
         faux= f
         f=0.
         j2=j
         do 22 k=1,j
            f= bico(n,k)*0.5**n + f
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
