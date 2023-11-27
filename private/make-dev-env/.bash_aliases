alias cls="clear"
alias cds='ssh root@lifestone.net'
alias ffs='sftp root@lifestone.net'
alias deploy='bash /home/haim/server_src/private/deploy_tol.bash'
alias venv='source /home/www-data/py38env/bin/activate'
alias cd2="cd home/www-data/py38env/web2py/applications/"
alias r="cd ~/client_src;au run --env dev --watch"
alias rs="cd ~/client_src;au run --env rishpon --watch"
alias ry="cd ~/client_src;au run --env yiron --watch"
alias rgh='cd ~/client_src;au run --env ganhaim --watch'
alias rg='cd ~/client_src;au run --env gbs --watch'
alias rp="cd ~/client_src;au run --env push --watch"
alias rr="replace \.\.\/scripts\/ /scripts/ --  scripts/vendor-bundle.js"
alias cdc="cd ~/server_src"
alias cda="cd ~/client_src"
alias psg="sudo su - postgres"
alias bkp_apps_data="rsync -avz -e ssh root@tol.life::/apps_data/$1 :~/server_data/$1"
alias mig="python /home/haim/server_src/private/localtimeline.py"