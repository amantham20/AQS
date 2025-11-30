package main

import (
	"bufio"
	"flag"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strings"

	"github.com/sahilm/fuzzy"
)

const maxLines = 1000

func main() {
	dryRun := flag.Bool("d", false, "Dry run: print selected command without executing")
	flag.BoolVar(dryRun, "dry-run", false, "Dry run: print selected command without executing")
	flag.Usage = func() {
		fmt.Fprintf(os.Stderr, "AQS — fuzzy search recent commands\n\n")
		fmt.Fprintf(os.Stderr, "Usage: aqs [options] [query]\n\n")
		fmt.Fprintf(os.Stderr, "Opens fzf picker and executes the selected command.\n")
		fmt.Fprintf(os.Stderr, "Use -d/--dry-run to only print without executing.\n\n")
		fmt.Fprintf(os.Stderr, "Options:\n")
		flag.PrintDefaults()
	}
	flag.Parse()

	query := ""
	if flag.NArg() > 0 {
		query = strings.Join(flag.Args(), " ")
	}

	paths := detectHistoryPaths()
	items := readHistory(paths)
	if len(items) == 0 {
		fmt.Fprintln(os.Stderr, "No history found.")
		os.Exit(2)
	}

	// If query provided, pre-sort by similarity
	if query != "" {
		items = sortBySimilarity(query, items)
	}

	// Open fzf interactive picker
	selected := callFzf(items, query, query != "")
	if selected == "" {
		if _, err := exec.LookPath("fzf"); err != nil {
			fmt.Fprintln(os.Stderr, "fzf not found. Install fzf: brew install fzf")
		}
		os.Exit(1)
	}

	// Print selected command
	fmt.Println(selected)

	// Execute unless dry-run
	if !*dryRun {
		os.Exit(runCommand(selected))
	}
}

func detectHistoryPaths() []string {
	home, err := os.UserHomeDir()
	if err != nil {
		return nil
	}

	return []string{
		filepath.Join(home, ".bash_history"),
		filepath.Join(home, ".zsh_history"),
		filepath.Join(home, ".local", "share", "fish", "fish_history"),
	}
}

func readHistory(paths []string) []string {
	var cmds []string

	for _, p := range paths {
		file, err := os.Open(p)
		if err != nil {
			continue
		}

		isFish := strings.Contains(p, "fish_history")
		scanner := bufio.NewScanner(file)
		// Increase buffer size for long lines
		buf := make([]byte, 0, 64*1024)
		scanner.Buffer(buf, 1024*1024)

		for scanner.Scan() {
			line := scanner.Text()
			if isFish {
				// fish history: lines like "- cmd: git status"
				line = strings.TrimSpace(line)
				if strings.HasPrefix(line, "- cmd:") {
					cmd := strings.TrimSpace(strings.TrimPrefix(line, "- cmd:"))
					if cmd != "" {
						cmds = append(cmds, cmd)
					}
				}
			} else {
				// Handle zsh extended history format: ": timestamp:0;command"
				if strings.HasPrefix(line, ": ") && strings.Contains(line, ";") {
					idx := strings.Index(line, ";")
					if idx != -1 {
						line = line[idx+1:]
					}
				}
				line = strings.TrimSpace(line)
				if line != "" {
					cmds = append(cmds, line)
				}
			}
		}
		file.Close()
	}

	// Keep only the last maxLines entries
	if len(cmds) > maxLines {
		cmds = cmds[len(cmds)-maxLines:]
	}

	// Dedupe preserving most recent — iterate reversed and keep first occurrences
	seen := make(map[string]bool)
	var uniq []string
	for i := len(cmds) - 1; i >= 0; i-- {
		cmd := cmds[i]
		if seen[cmd] {
			continue
		}
		seen[cmd] = true
		uniq = append(uniq, cmd)
	}

	return uniq
}

type scoredItem struct {
	item   string
	score1 int // primary score (higher = better)
	score2 int // secondary score (lower = better, typically length)
}

func sortBySimilarity(query string, items []string) []string {
	queryLower := strings.ToLower(query)

	scored := make([]scoredItem, len(items))
	for i, item := range items {
		scored[i] = scoredItem{
			item:   item,
			score1: 0,
			score2: len(item),
		}
		itemLower := strings.ToLower(item)

		// Exact match gets highest score
		if itemLower == queryLower {
			scored[i].score1 = 1000
			scored[i].score2 = 0
			continue
		}

		// Starts with query (command itself matches)
		if strings.HasPrefix(itemLower, queryLower+" ") || strings.HasPrefix(itemLower, queryLower+"\t") {
			scored[i].score1 = 900
			continue
		}

		// Query is the first word/command
		words := strings.Fields(itemLower)
		firstWord := ""
		if len(words) > 0 {
			firstWord = words[0]
		}

		if firstWord == queryLower {
			scored[i].score1 = 850
			continue
		}

		// First word starts with query
		if strings.HasPrefix(firstWord, queryLower) {
			scored[i].score1 = 800
			continue
		}

		// Query appears as a whole word somewhere
		for _, w := range words {
			if w == queryLower {
				scored[i].score1 = 700
				break
			}
		}
		if scored[i].score1 == 700 {
			continue
		}

		// Query is a substring at word boundary
		if strings.Contains(itemLower, " "+queryLower) || strings.Contains(itemLower, "/"+queryLower) {
			scored[i].score1 = 600
			continue
		}

		// General substring match
		if idx := strings.Index(itemLower, queryLower); idx != -1 {
			scored[i].score1 = 500 - idx
			continue
		}

		// Fuzzy match fallback using sahilm/fuzzy
		matches := fuzzy.Find(queryLower, []string{itemLower})
		if len(matches) > 0 {
			scored[i].score1 = matches[0].Score
		}
	}

	// Sort by score descending, then by length ascending
	sort.Slice(scored, func(i, j int) bool {
		if scored[i].score1 != scored[j].score1 {
			return scored[i].score1 > scored[j].score1
		}
		return scored[i].score2 < scored[j].score2
	})

	result := make([]string, len(scored))
	for i, s := range scored {
		result[i] = s.item
	}
	return result
}

func callFzf(items []string, initialQuery string, useCustomSort bool) string {
	fzfPath, err := exec.LookPath("fzf")
	if err != nil {
		return ""
	}

	args := []string{"--ansi", "--reverse", "--tiebreak=index"}
	if useCustomSort {
		args = append(args, "--no-sort")
	}
	if initialQuery != "" {
		args = append(args, "--query", initialQuery)
	}

	cmd := exec.Command(fzfPath, args...)
	cmd.Stderr = os.Stderr

	stdin, err := cmd.StdinPipe()
	if err != nil {
		return ""
	}

	stdout, err := cmd.StdoutPipe()
	if err != nil {
		return ""
	}

	if err := cmd.Start(); err != nil {
		return ""
	}

	// Write items to fzf stdin
	go func() {
		for _, item := range items {
			fmt.Fprintln(stdin, item)
		}
		stdin.Close()
	}()

	// Read selected item
	scanner := bufio.NewScanner(stdout)
	var selected string
	if scanner.Scan() {
		selected = scanner.Text()
	}

	cmd.Wait()
	return strings.TrimSpace(selected)
}

func runCommand(cmd string) int {
	fmt.Fprintf(os.Stderr, "Running: %s\n", cmd)

	// Detect shell
	shell := os.Getenv("SHELL")
	if shell == "" {
		shell = "/bin/sh"
	}

	proc := exec.Command(shell, "-c", cmd)
	proc.Stdin = os.Stdin
	proc.Stdout = os.Stdout
	proc.Stderr = os.Stderr

	if err := proc.Run(); err != nil {
		if exitErr, ok := err.(*exec.ExitError); ok {
			return exitErr.ExitCode()
		}
		fmt.Fprintf(os.Stderr, "Error running command: %v\n", err)
		return 1
	}
	return 0
}
