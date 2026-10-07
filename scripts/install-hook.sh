#!/usr/bin/env bash
# one-time: makes git run scripts/check.sh before every commit
cd "$(git rev-parse --show-toplevel)"
printf "#!/usr/bin/env bash\nexec bash scripts/check.sh\n" > .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
echo "pre-commit hook installed"
