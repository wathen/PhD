%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% This program tests the convergence properties of our mixed implementation
%
% NOTE: The data has to be adjusted in data_m.m and the exact solution is
% in exact_m.m
% 
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

disp('adjust the data and exact solution in data.m and exact.m')
  

ref=4;                      % number of global refinements
clear L2_error_u   
clear curl_error_u 
clear L2_error_p   
clear H1_error_p   
clear l_num        
clear DoFs        

% initialize a mesh
[p,e,t]=initmesh('squareg','hmax',1.5);

for i=1:ref

  i

  [p,e,t]=refinemesh('squareg',p,e,t,'regular');
    
  % find and number the edges
  [te, be, edge_num]=edges(t,e);

  % identify interior/boundary edges
  [list_of_int_edges,list_of_bnd_edges]=sort_edge_dofs(te,be,edge_num);

  % identify interior/boundary nodes 
  [list_of_int_nodes,list_of_bnd_nodes]=sort_nodal_dofs(p,e);
 
  % dimensions
  %
  int_edge_num=length(list_of_int_edges);
  bnd_edge_num=length(list_of_bnd_edges);
  int_node_num =length(list_of_int_nodes);
  bnd_node_num = length(list_of_bnd_nodes);
  edge_num=int_edge_num+bnd_edge_num;
  node_num=int_node_num+bnd_node_num;

  % permutations of interior/boundary dofs

  clear edge_index_reverse; 
  edge_index=[list_of_int_edges,list_of_bnd_edges];
  edge_index_reverse(edge_index(:))=1:edge_num;

  clear node_index_reverse;
  node_index=[list_of_int_nodes,list_of_bnd_nodes];
  node_index_reverse(node_index(:))=1:node_num;

  % get our matrices
  [A11,M11,L1,S11,Q11,B11,u_b,p_b]=our_matrices(p,t,te,list_of_int_edges,list_of_bnd_edges,list_of_int_nodes,list_of_bnd_nodes);



  %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
  %
  % Mixed System
  %
  %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

  K = [A11 B11; B11' sparse(int_node_num,int_node_num)];
  F = [ L1; zeros(int_node_num,1)];

  %%% solution of the KKT system

  cond(full(A11+M11)),pause
  [sol] = K\F;



  %%%% electric field and potential (only interior)


  u_i = sol(1:int_edge_num,1);
  p_i = sol(int_edge_num+1:length(sol), 1);

  u_per = [u_i;u_b];
  p_per = [p_i;p_b];

  % inverse permutation of interior/boundary edges
  edge_index=[list_of_int_edges,list_of_bnd_edges];
  node_index=[list_of_int_nodes,list_of_bnd_nodes];


  uh=u_per(edge_index_reverse);
  ph=p_per(node_index_reverse);



  [L2_error_u(i),curl_error_u(i)] = uh_errors(p,t,te,uh)
  [L2_error_p(i),H1_error_p(i)] = ph_errors(p,t,ph)

  % compute number of elements
  l_num(i) = length(t);
    
  % compute number of degrees of freedom in u
  DoFs(i) = length(uh);


end



figure(1)
subplot(2,1,1)
loglog(l_num,L2_error_u,'o-',l_num,curl_error_u,'*-',l_num,l_num.^(-1/2),'r')
title('L2- and H(curl)-error of uh vs. number of elements')
legend('L2-error','H(curl)-error','Order 1')
xlabel('number of elements in mesh')
ylabel('errors')
grid on

subplot(2,1,2)
loglog(l_num,L2_error_p,'o-',l_num,H1_error_p,'*-',l_num,l_num.^(-1/2),l_num,l_num.^(-1),'-.' )
title('L2- and H1-error of ph vs. number of elements')
legend('L2-error','H1-error','Order 1', 'Order 2')
xlabel('number of elements in mesh')
ylabel('errors')
grid on







