package 'nginx' do
  action :install
end

service 'nginx' do
  action [:enable, :start]
end

file '/var/www/html/index.html' do
  content "Convergido con Cinc en #{node['kernel']['machine']}\n"
end
