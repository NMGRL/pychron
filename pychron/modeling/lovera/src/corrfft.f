C	CORRALL.F   CALCULATION OF CROSS-CORRELATION USING THE FFT     
C  crosscorrelation using the fft
    
      parameter(ns=128,nc=100,ns2=256)
      dimension cros(ns2),cor1(ns2),cor2(ns2)
      dimension yy(ns),ar39(0:ns),age2(ns)
      dimension f39(0:ns),age(0:ns),xlogr(0:ns),cint(nc)
	dimension agem(ns,0:ns),xlgrm(ns,0:ns)
      dimension c1(nc),c2(nc),cc(nc,nc)
      external favr
	character  sname*50
	character*10 mname(100)
      open(unit=8,file='files.cl',status='old')
	open(unit=25,file='cross.dat')
	open(unit=28,file='ccross.dat')
      write(25,*)'crosscor   ','  #  ','   sample name   ',
     $'   fmin','   fmax'

	  x0 =  0.
	  mc = 15
c	  fmin = 0.02
c	  fmax = 0.82
       
C  READ THE FILES AND MAKE MATRIX
	n = 1
1     read(8,'(A50)',END=300)sname
      read(8,*)fmin,fmax
	kn=name(sname)  
	mname(n)=sname(1:kn)
      open(unit=22,file=sname(1:kn)//'_age-cl.smp',status='old')
      open(unit=23,file=sname(1:kn)//'_log.smp',status='old')
        xl = fmax - fmin

      do 10 j=1,ns
          read(23,*,END=20)ar39(j),xlogr(j)
          read(23,*,END=20)ar39(j),xlogr(j)
          read(22,*,END=20)ar39(j),age(j)
          read(22,*,END=20)ar39(j),age(j)
          f39(j)=(ar39(j)+ar39(j-1))/200.d0
10    continue
20    ni=j
      do 12 k=1,ni-1
	  read(22,*,ERR=22,END=16)ar39(j),age2(ni-k)
	  read(22,*,END=16)ar39(j),age2(ni-k)
12    continue
      goto 16
22    do 14 k=1,ni-1
	    read(22,*,END=16)ar39(j),age2(k)
	    read(22,*,END=16)ar39(j),age2(k)
14    continue
16    do 18 j=1,ni-1
        age(j)=(age(j)+age2(j))/2.
c	  write(10,*)f39(j),age(j)
18	continue
	f39(ni)=1.d0
      age(ni)=age(ni-1)
      xlogr(ni)=xlogr(ni-1)
      close(22)
      close(23)
      call chebft(x0,xl,c1,mc,favr,f39,age,ni,fmin)
      call chebft(x0,xl,c2,mc,favr,f39,xlogr,ni,fmin)
      call chint(x0,xl,c1,cint,mc)
      aget = chebev(x0,xl,cint,mc,xl)/xl
      call chint(x0,xl,c2,cint,mc)
      xlogt = chebev(x0,xl,cint,mc,xl)/xl     
	dx=xl/(ns-1)
      do 40 j=1,ns
         yy(j)=dx*(j-1)
         if(yy(j).gt.xl)yy(j)=xl
         agem(n,j)= chebev(x0,xl,c1,mc,yy(j))-aget
         xlgrm(n,j)=chebev(x0,xl,c2,mc,yy(j))-xlogt
40    continue
      agem(n,0)=fmin
	xlgrm(n,0)=fmax
	n=n+1
	goto 1

C  CALCULATION OF CROSS AND PERMUTATIONS

300      Do 70 k1=1,n-1
          do 74 j=1,ns
	       age(j)=agem(k1,j)
	       xlogr(j)=xlgrm(k1,j)
74	    continue
  
           call correl(age,xlogr,ns,cros)
           call correl(age,age,ns,cor1)
           call correl(xlogr,xlogr,ns,cor2)
           cornor=sqrt(cor1(1)*cor2(1))
	     cc(k1,k1) = cros(1)/cornor
           fmin = agem(k1,0)
	     fmax = xlgrm(k1,0)
		 dx=(fmax-fmin)/(ns-1)
          write(25,120)cc(k1,k1),mname(k1),fmin,fmax
	    do 76 j=-ns/2,-1
	      nj=ns+j+1
	      write(28,*)dx*(j),cros(nj)/cornor,cor1(nj)/cor1(1),
     $	  cor2(nj)/cor2(1)
76        continue
	    do 78 j=1,ns/2
	      nj=j
	      write(28,*)dx*(j-1),cros(nj)/cornor,cor1(nj)/cor1(1),
     $	  cor2(nj)/cor2(1)
78        continue
          write(28,*)'& ',mname(k1)
70    continue
120   format(1x,f12.6,a15,2f12.6)
100   format(1x,f8.4,5f12.6)

        stop
        end

      subroutine correl(data1,data2,n,ans)
      parameter(nmax=8192)
      dimension data1(n),data2(n)
      complex fft(nmax),ans(n)
      call twofft(data1,data2,fft,ans,n)
      no2=float(n)/2.0
      do 11 i=1,n/2+1
        ans(i)=fft(i)*conjg(ans(i))/no2
11    continue
      ans(1)=cmplx(real(ans(1)),real(ans(n/2+1)))
      call realft(ans,n/2,-1)
      return
      end

      subroutine twofft(data1,data2,fft1,fft2,n)
      dimension data1(n),data2(n)
      complex fft1(n),fft2(n),h1,h2,c1,c2
      c1=cmplx(0.5,0.0)
      c2=cmplx(0.0,-0.5)
      do 11 j=1,n
        fft1(j)=cmplx(data1(j),data2(j))
11    continue
      call four1(fft1,n,1)
      fft2(1)=cmplx(aimag(fft1(1)),0.0)
      fft1(1)=cmplx(real(fft1(1)),0.0)
      n2=n+2
      do 12 j=2,n/2+1
        h1=c1*(fft1(j)+conjg(fft1(n2-j)))
        h2=c2*(fft1(j)-conjg(fft1(n2-j)))
        fft1(j)=h1
        fft1(n2-j)=conjg(h1)
        fft2(j)=h2
        fft2(n2-j)=conjg(h2)
12    continue
      return
      end

      subroutine realft(data,n,isign)
      real*8 wr,wi,wpr,wpi,wtemp,theta
      dimension data(*)
      theta=6.28318530717959d0/2.0d0/dble(n)
      c1=0.5
      if (isign.eq.1) then
        c2=-0.5
        call four1(data,n,+1)
      else
        c2=0.5
        theta=-theta
      endif
      wpr=-2.0d0*dsin(0.5d0*theta)**2
      wpi=dsin(theta)
      wr=1.0d0+wpr
      wi=wpi
      n2p3=2*n+3
      do 11 i=2,n/2+1
        i1=2*i-1
        i2=i1+1
        i3=n2p3-i2
        i4=i3+1
        wrs=sngl(wr)
        wis=sngl(wi)
        h1r=c1*(data(i1)+data(i3))
        h1i=c1*(data(i2)-data(i4))
        h2r=-c2*(data(i2)+data(i4))
        h2i=c2*(data(i1)-data(i3))
        data(i1)=h1r+wrs*h2r-wis*h2i
        data(i2)=h1i+wrs*h2i+wis*h2r
        data(i3)=h1r-wrs*h2r+wis*h2i
        data(i4)=-h1i+wrs*h2i+wis*h2r
        wtemp=wr
        wr=wr*wpr-wi*wpi+wr
        wi=wi*wpr+wtemp*wpi+wi
11    continue
      if (isign.eq.1) then
        h1r=data(1)
        data(1)=h1r+data(2)
        data(2)=h1r-data(2)
      else
        h1r=data(1)
        data(1)=c1*(h1r+data(2))
        data(2)=c1*(h1r-data(2))
        call four1(data,n,-1)
      endif
      return
      end

      subroutine four1(data,nn,isign)
      real*8 wr,wi,wpr,wpi,wtemp,theta
      dimension data(*)
      n=2*nn
      j=1
      do 11 i=1,n,2
        if(j.gt.i)then
          tempr=data(j)
          tempi=data(j+1)
          data(j)=data(i)
          data(j+1)=data(i+1)
          data(i)=tempr
          data(i+1)=tempi
        endif
        m=n/2
1       if ((m.ge.2).and.(j.gt.m)) then
          j=j-m
          m=m/2
        go to 1
        endif
        j=j+m
11    continue
      mmax=2
2     if (n.gt.mmax) then
        istep=2*mmax
        theta=6.28318530717959d0/(isign*mmax)
        wpr=-2.d0*dsin(0.5d0*theta)**2
        wpi=dsin(theta)
        wr=1.d0
        wi=0.d0
        do 13 m=1,mmax,2
          do 12 i=m,n,istep
            j=i+mmax
            tempr=sngl(wr)*data(j)-sngl(wi)*data(j+1)
            tempi=sngl(wr)*data(j+1)+sngl(wi)*data(j)
            data(j)=data(i)-tempr
            data(j+1)=data(i+1)-tempi
            data(i)=data(i)+tempr
            data(i+1)=data(i+1)+tempi
12        continue
          wtemp=wr
          wr=wr*wpr-wi*wpi+wr
          wi=wi*wpr+wtemp*wpi+wi
13      continue
        mmax=istep
      go to 2
      endif
      return
      end
      subroutine fourn(data,nn,ndim,isign)
      real*8 wr,wi,wpr,wpi,wtemp,theta
      dimension nn(ndim),data(*)
      ntot=1
      do 11 idim=1,ndim
        ntot=ntot*nn(idim)
11    continue
      nprev=1
      do 18 idim=1,ndim
        n=nn(idim)
        nrem=ntot/(n*nprev)
        ip1=2*nprev
        ip2=ip1*n
        ip3=ip2*nrem
        i2rev=1
        do 14 i2=1,ip2,ip1
          if(i2.lt.i2rev)then
            do 13 i1=i2,i2+ip1-2,2
              do 12 i3=i1,ip3,ip2
                i3rev=i2rev+i3-i2
                tempr=data(i3)
                tempi=data(i3+1)
                data(i3)=data(i3rev)
                data(i3+1)=data(i3rev+1)
                data(i3rev)=tempr
                data(i3rev+1)=tempi
12            continue
13          continue
          endif
          ibit=ip2/2
1         if ((ibit.ge.ip1).and.(i2rev.gt.ibit)) then
            i2rev=i2rev-ibit
            ibit=ibit/2
          go to 1
          endif
          i2rev=i2rev+ibit
14      continue
        ifp1=ip1
2       if(ifp1.lt.ip2)then
          ifp2=2*ifp1
          theta=isign*6.28318530717959d0/(ifp2/ip1)
          wpr=-2.d0*dsin(0.5d0*theta)**2
          wpi=dsin(theta)
          wr=1.d0
          wi=0.d0
          do 17 i3=1,ifp1,ip1
            do 16 i1=i3,i3+ip1-2,2
              do 15 i2=i1,ip3,ifp2
                k1=i2
                k2=k1+ifp1
                tempr=sngl(wr)*data(k2)-sngl(wi)*data(k2+1)
                tempi=sngl(wr)*data(k2+1)+sngl(wi)*data(k2)
                data(k2)=data(k1)-tempr
                data(k2+1)=data(k1+1)-tempi
                data(k1)=data(k1)+tempr
                data(k1+1)=data(k1+1)+tempi
15            continue
16          continue
            wtemp=wr
            wr=wr*wpr-wi*wpi+wr
            wi=wi*wpr+wtemp*wpi+wi
17        continue
          ifp1=ifp2
        go to 2
        endif
        nprev=n*nprev
18    continue
      return
      end

       subroutine chebft(a,b,c,n,func,r39,f39,ni,fmin)
       parameter (nmax=100, pi=3.141592653589793d0, ns=100)
      dimension c(n),f(nmax),r39(0:ns),f39(0:ns)
      bma=0.5d00*(b-a)
      bpa=0.5d00*(b+a)
      do 11 k=1,n
        y=dcos(pi*(k-0.5d0)/n)
        f(k)=func(r39,f39,ni,fmin,y*bma+bpa)
11    continue
      fac=2.d0/n
      do 13 j=1,n
        sum=0.d0
        do 12 k=1,n
          sum=sum+f(k)*cos((pi*(j-1))*((k-0.5d0)/n))
12      continue
        c(j)=fac*sum
13    continue
      return
      end

      function chebev(a,b,c,m,x)
      dimension c(m)
      if ((x-a)*(x-b).gt.0.) then
         stop 'ERROR(CHEBEV): x not in range .'
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

      function favr(fx,fy,ni,fmin,xa)
      parameter (ns=100)
      dimension fx(0:ns),fy(0:ns)
      do 10 j=1,ni
        x=xa+fmin
        if(fx(j).ge.x.and.fx(j-1).lt.x)then
          slope =  (fy(j)-fy(j-1))/(fx(j)-fx(j-1))
          favr=fy(j-1)+ slope * (x-fx(j-1))
          return
       endif
10    continue
      end

      subroutine chint(a,b,c,cint,n)
      dimension c(n),cint(n)
      con=0.25*(b-a)
      sum=0.
      fac=1.
      do 11 j=2,n-1
        cint(j)=con*(c(j-1)-c(j+1))/(j-1)
        sum=sum+fac*cint(j)
        fac=-fac
11    continue
      cint(n)=con*c(n-1)/(n-1)
      sum=sum+fac*cint(n)
      cint(1)=2.*sum
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

