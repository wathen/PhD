close all
clear

%%
n = 4;
XX = linspace(0,1,n);
[x,y] = meshgrid(XX,XX);
FEMmesh.a = 0;FEMmesh.b = 1;
FEMmesh.n =n;
h = (FEMmesh.b-FEMmesh.a)/(FEMmesh.n-1);
t = TimeHarmonic;
[FEMmesh] = t.GetMesh(FEMmesh);

%%
figure()
plotGrid2D(x,y,'col','r','knots','off','linewidth',2,'markersize',20,'gridx',n,'gridy',n)
x = x(:,1:n-1)';y = y(1:n-1,:)';
X = x(:); Y = y(:);
ii = 0;
jj = 1;
for i = 1:(n-1)^2
    
    ii = ii +1;
     text('Interpreter','latex',...
	'String',num2str(i),...
	'Position',[ii/(n-1)-h/2 jj/(n-1)-h/2],...
	'FontSize',16)
     if 0 == mod(ii,n-1)
        ii = 0; 
        jj = jj+1;
     end
end

for i = 1:length(FEMmesh.X)

    a = ['$e_{',num2str(i),'}$'];
    text('Interpreter','latex',...
	'String',a,...
	'Position',[FEMmesh.X(i)-h/20 FEMmesh.Y(i)-h/20],...
	'FontSize',14)
end

axis([FEMmesh.a-.1 FEMmesh.b+.1 FEMmesh.a-.1 FEMmesh.b+.1])

%%
shift = .3;
FigHandle = figure;
  set(FigHandle, 'Position', [100, 100, 1200, 600]);
plotGrid2D([1/3 2/3;1/3 2/3],[1/3 1/3;2/3 2/3],'col','r','knots','off','linewidth',2,'markersize',20,'gridx',n,'gridy',n)
plotGrid2D([0 0;1 1]',[1 1; 2 2]+shift,'col','r','knots','off','linewidth',2,'markersize',20,'gridx',n,'gridy',n)
axis([0-.2 2+.2+shift 0-.2 1+.2])
text('Interpreter','latex',...
	'String','$\rightarrow$',...
	'Position',[.85 .5],...
	'FontSize',70)


% for i = 1:4
text('Interpreter','latex',...
	'String','$((i-1)h,(j-1)h)$',...
	'Position',[1/3-.19 1/3-.05],...
	'FontSize',14)
text('Interpreter','latex',...
	'String','$(ih,(j-1)h)$',...
	'Position',[2/3-.1 1/3-.05],...
	'FontSize',14)
text('Interpreter','latex',...
	'String','$((i-1)h,jh)$',...
	'Position',[1/3-.13 2/3+.05],...
	'FontSize',14)
text('Interpreter','latex',...
	'String','$(ih,jh)$',...
	'Position',[2/3-.05 2/3+.05],...
	'FontSize',14)

text('Interpreter','latex',...
	'String','$(0,0)$',...
	'Position',[1+shift-.05 0-.05],...
	'FontSize',14)
text('Interpreter','latex',...
	'String','$(1,0)$',...
	'Position',[2+shift-.05 0-.05],...
	'FontSize',14)
text('Interpreter','latex',...
	'String','$(0,1)$',...
	'Position',[1+shift-.05 1+.05],...
	'FontSize',14)
text('Interpreter','latex',...
	'String','$(1,1)$',...
	'Position',[2+shift-.05 1+.05],...
	'FontSize',14)

% end



plot(1/3, 1/3,'ko','MarkerFaceColor','k')
plot(1/3, 2/3,'ko','MarkerFaceColor','k')
plot(2/3, 1/3,'ko','MarkerFaceColor','k')
plot(2/3, 2/3,'ko','MarkerFaceColor','k')


plot( 1+shift,0,'ko','MarkerFaceColor','k')
plot(2+shift, 0,'ko','MarkerFaceColor','k')
plot(1+shift, 1,'ko','MarkerFaceColor','k')
plot(2+shift, 1,'ko','MarkerFaceColor','k')

% axis off

%%


FigHandle = figure;
  set(FigHandle, 'Position', [100, 100, 800, 800]);
plotGrid2D([1/4 3/4;1/4 3/4],[1/4 1/4;3/4 3/4],'col','r','knots','off','linewidth',2,'markersize',20,'gridx',n,'gridy',n)
axis([.1 .9 .1 .9])
plot( 3/4,1/4,'ko','MarkerFaceColor','k')
plot(1/4, 1/4,'ko','MarkerFaceColor','k')
plot(1/4, 3/4,'ko','MarkerFaceColor','k')
plot(3/4, 3/4,'ko','MarkerFaceColor','k')





text('Interpreter','latex',...
	'String','$\vec{\phi_{e_1}}$',...
	'Position',[.5-.02 .21],...
	'FontSize',40)

text('Interpreter','latex',...
	'String','$\vec{\phi_{e_2}}$',...
	'Position',[.77 .5],...
	'FontSize',40)


text('Interpreter','latex',...
	'String','$\vec{\phi_{e_3}}$',...
	'Position',[.5-.02 .79],...
	'FontSize',40)

text('Interpreter','latex',...
	'String','$\vec{\phi_{e_4}}$',...
	'Position',[.16 .5],...
	'FontSize',40)

%%


FigHandle = figure;
  set(FigHandle, 'Position', [100, 100, 800, 800]);
plotGrid2D([1/4 3/4;1/4 .5],[1/4 1/4;3/4 .5],'col','r','knots','off','linewidth',2,'markersize',20,'gridx',n,'gridy',n)
plot( 3/4,1/4,'ko','MarkerFaceColor','k')
plot(1/4, 1/4,'ko','MarkerFaceColor','k')
plot(1/4, 3/4,'ko','MarkerFaceColor','k')

axis([.1 .9 .1 .9])


text('Interpreter','latex',...
	'String','$\vec{\phi_{e_1}}$',...
	'Position',[.5-.02 .21],...
	'FontSize',40)

text('Interpreter','latex',...
	'String','$\vec{\phi_{e_2}}$',...
	'Position',[.54 .54],...
	'FontSize',40)


text('Interpreter','latex',...
	'String','$\vec{\phi_{e_3}}$',...
	'Position',[.16 .5],...
	'FontSize',40)