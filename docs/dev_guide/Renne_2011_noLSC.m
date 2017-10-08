% clear workspace
clear
clf
format long
M = 10^4; %this may be increased depending on your system

%Global Values
el = 5.757*10^(-11);    %input value of electron capture decay constant
sel = 1.600*10^(-13);   %input uncertainty of electron capture decay constant
vel = el + sel*randn(M,1);

b = 4.955*10^(-10);     %input value of beta decay constant
sb = 1.340*10^(-12);    %input uncertainty of beta decay constant
vb = b + sb*randn(M,1);

T = 5.531*10^(-10);     %input value of total decay constant
sT = 1.350*10^(-12);    %input uncertainty of total decay constant
vT = T + sT*randn(M,1);

F = 0.001642;           %input value of 40Ar*/40K for mineral standard
sF = 4.50*10^(-6);      %input uncertainty of 40Ar*/40K for mineral standard
vF = F + sF.*randn(M,1);

%load age and uncertainty column vectors. These must have the same length.
A = xlsread('age_uncert.xls'); %where "age_uncert" is an excel file with column A=age, column B=analytical uncertainty in age
[m,n] = size(A);
age = A(:,1);
uncert = A(:,2);

%linear R value calculation
FCs_orig = 28.020;  %original age for FCs, in Ma, (Renne et al., 1998)
T_orig = 5.543*10^(-10); % original total decay constant
ex_orig = (exp(T.*FCs_orig.*10^6))-1; %exp(lambda*t)-1
ex = (exp(T.*(age').*10^6))-1; %exp(lambda*t)-1
R = ex./ex_orig;
sR = T_orig.*exp(T_orig.*(age').*10^6).*(uncert').*10^6./ex_orig;
R_mc = repmat(R,M,1);
sR_mc = repmat(sR,M,1);
vR = R_mc + sR_mc.*randn(M,m); % R uncertainty for Monte Carlo

% Age calculation
t = log(((T./el).*F.*R)+1)./(T.*10^6);

% Linear uncertainty propagation

% partial derivatives 
pd_el = -(1./T).*(t.*10^6 + (b.*F.*R./((el.^2).*exp(T.*t.*10^6))));
pd_b = (1./T).*((F.*R./(el.*exp(T.*t.*10^6)))-(t.*10^6));
pd_F = R./(el.*exp(T.*t.*10^6));
pd_R = F./(el.*exp(T.*t.*10^6));

% (partial derivatives x sigma)^2
pd_el2 = (pd_el.*sel).^2;
pd_b2 = (pd_b.*sb).^2;
pd_F2 = (pd_F.*sF).^2;
pd_R2 = (pd_R.*sR).^2;

sum_pd = pd_el2 + pd_b2 + pd_F2 + pd_R2;

% covariances
cov_F_el = 7.1903*10^(-19);
cov_F_b = -6.5839*10^(-19);
cov_el_b = -3.4711*10^(-26);

cov_F_el2 = 2.*cov_F_el.*pd_F.*pd_el;
cov_F_b2 = 2.*cov_F_b.*pd_F.*pd_b;
cov_el_b = 2.*cov_el_b.*pd_el.*pd_b;

sum_cov = cov_F_el2 + cov_F_b2 + cov_el_b;

sum = sum_pd + sum_cov;


% uncertainty in Age (Ma)
st = sqrt(sum)/10^6; %linear
vT_mc = repmat(vT,1,m);
vF_mc = repmat(vF,1,m);
vel_mc = repmat(vel,1,m);
t_mc = (log(vT_mc./vel_mc.*vF_mc.*vR + 1)).*(1./vT_mc)./10^6;

hist(t_mc(:,1)) %plot histogram of the age in the first row of input file

%output variable is 'recalc_age' with 4 columns (linear age, linear
%uncertainty, Monte Carlo age, Monte Carlo uncertainty, in that order)
recalc_age = [(t);(st);(mean(t_mc));(std(t_mc))]';
