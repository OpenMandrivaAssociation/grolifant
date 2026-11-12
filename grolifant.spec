Name:		grolifant
Version:	5.12.7
Release:	1
Summary:	Support library for Gradle plugins
Group:		Development/Java
License:	MPL-2.0
URL:		https://gitlab.com/ysb33rOrg/gradle/grolifant
# Tag RELEASE_5_12_7. asciidoctor5-jvm-core-plugin 5.1.0 compiles
# against grolifant5-core and loads grolifant5-rawhide at runtime.
# Upstream builds with Gradle. This package compiles the main sources
# with Groovy's FileSystemCompiler. The Gradle tool is not invoked.
# Gradle 8.11 has no no-arg UnknownDomainObjectException constructor,
# so @InheritConstructors cannot emit UnknownStateObjectException.
Source0:	grolifant-%{version}.tar.gz
Patch0:		grolifant-gradle8-constructors.patch

BuildArch:	noarch
BuildRequires:	java-current-devel
BuildRequires:	gradle
BuildRequires:	apache-groovy
BuildRequires:	antlr4
BuildRequires:	objectweb-asm
BuildRequires:	picocli
BuildRequires:	jansi
BuildRequires:	apache-commons-io
BuildRequires:	ant-lib
BuildRequires:	slf4j2
BuildRequires:	sysjar
BuildRequires:	javapackages-filesystem
Requires:	gradle
Requires:	apache-groovy

%description
org.ysb33r.gradle:grolifant5-core, grolifant5-rawhide, and
grolifant5-herd %{version}. CaseFormats converts between kebab and
snake case. The main sources are compiled with FileSystemCompiler
at bytecode 11. The Gradle tool is not invoked.

%prep
%autosetup -n grolifant-RELEASE_5_12_7 -p1
find . -type f \( -name '*.jar' -o -name '*.class' -o -name '*.so' -o -name '*.node' -o -name '*.wasm' \) -print > binaries.list
find . -type d -name '*.jar' -print >> binaries.list
if [ -s binaries.list ]; then
	cat binaries.list
	exit 1
fi
find grolifant-core/src/main -type f \( -name '*.groovy' -o -name '*.java' \) | sort > core.list
find grolifant-rawhide/src/main -type f \( -name '*.groovy' -o -name '*.java' \) | sort > rawhide.list
test "$(wc -l < core.list)" -eq 257
test "$(grep -c '\.groovy$' core.list)" -eq 136
test "$(grep -c '\.java$' core.list)" -eq 121
test "$(wc -l < rawhide.list)" -eq 8
test "$(grep -c '\.groovy$' rawhide.list)" -eq 4
test "$(grep -c '\.java$' rawhide.list)" -eq 4
grep -F -q 'super(message)' grolifant-core/src/main/groovy/org/ysb33r/grolifant5/api/errors/UnknownStateObjectException.groovy
if grep -q InheritConstructors grolifant-core/src/main/groovy/org/ysb33r/grolifant5/api/errors/UnknownStateObjectException.groovy; then
	exit 1
fi
grep -F -q '@@GROLIFANT_VERSION@@' grolifant-core/src/main/resources/META-INF/grolifant/version.properties
grep -F -q '@@VERSION@@' grolifant-herd/src/main/resources/META-INF/grolifant5-herd.properties

%build
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
tool_cp=%{_javadir}/apache-groovy.jar
for extra in \
	%{_javadir}/antlr4-runtime.jar \
	%{_javadir}/asm.jar \
	%{_javadir}/asm-commons.jar \
	%{_javadir}/asm-tree.jar \
	%{_javadir}/asm-util.jar \
	%{_javadir}/asm-analysis.jar \
	%{_javadir}/picocli.jar \
	/usr/lib/java/jansi/jansi.jar
do
	test -s "$extra"
	tool_cp=$tool_cp:$extra
done
gradle_cp=
for j in %{_datadir}/gradle/lib/*.jar %{_datadir}/gradle/lib/plugins/*.jar; do
	test -s "$j"
	base=$(basename "$j")
	case "$base" in
	antlr4-runtime-*|asm-9*.jar|asm-commons-*|asm-tree-*|asm-util-*|asm-analysis-*)
		continue
		;;
	esac
	if [ -z "$gradle_cp" ]; then
		gradle_cp=$j
	else
		gradle_cp=$gradle_cp:$j
	fi
done
test -n "$gradle_cp"

mkdir -p rawhide-classes
java -Dgroovy.target.bytecode=11 -cp "$tool_cp" org.codehaus.groovy.tools.FileSystemCompiler \
	--classpath "$tool_cp" -j '-J-release=11' -d rawhide-classes @rawhide.list
test "$(find rawhide-classes -name '*.class' | wc -l)" -eq 10
javap -v -classpath rawhide-classes org.ysb33r.grolifant5.api.remote.worker.WorkerExecutionException | grep -F -q 'major version: 55'
printf '%s\n' 'Manifest-Version: 1.0' 'Automatic-Module-Name: org.ysb33r.grolifant5.rawhide' > rawhide.mf
jar cfm grolifant5-rawhide.jar rawhide.mf -C rawhide-classes .
jar i grolifant5-rawhide.jar

src_cp=$gradle_cp:%{_javadir}/commons-io.jar:%{_javadir}/ant.jar:grolifant5-rawhide.jar
mkdir -p core-classes
java -Dgroovy.target.bytecode=11 -cp "$tool_cp:$src_cp" org.codehaus.groovy.tools.FileSystemCompiler \
	--classpath "$src_cp" -j '-J-release=11' -d core-classes @core.list
test "$(find core-classes -name '*.class' | wc -l)" -eq 528
javap -v -classpath core-classes org.ysb33r.grolifant5.api.core.CaseFormats | grep -F -q 'major version: 55'
javap -v -classpath core-classes org.ysb33r.grolifant5.api.core.StringTools | grep -F -q 'major version: 55'
javap -v -classpath core-classes org.ysb33r.grolifant5.api.errors.UnknownStateObjectException | grep -F -q 'major version: 55'
mkdir -p core-classes/META-INF/grolifant
sed \
	-e 's/@@GROLIFANT_VERSION@@/%{version}/' \
	-e 's/@@VERSION@@/%{version}/' \
	grolifant-core/src/main/resources/META-INF/grolifant/version.properties \
	> core-classes/META-INF/grolifant/version.properties
grep -qx 'grolifant=%{version}' core-classes/META-INF/grolifant/version.properties
if grep -q '@@' core-classes/META-INF/grolifant/version.properties; then
	exit 1
fi
printf '%s\n' 'Manifest-Version: 1.0' 'Automatic-Module-Name: org.ysb33r.grolifant5.core' > core.mf
jar cfm grolifant5-core.jar core.mf -C core-classes .
jar i grolifant5-core.jar
jar tf grolifant5-core.jar | grep -qx 'META-INF/grolifant/version.properties'
jar tf grolifant5-core.jar | grep -F -q 'org/ysb33r/grolifant5/api/core/CaseFormats.class'

mkdir -p herd-classes/META-INF
sed 's/@@VERSION@@/%{version}/' \
	grolifant-herd/src/main/resources/META-INF/grolifant5-herd.properties \
	> herd-classes/META-INF/grolifant5-herd.properties
grep -qx 'version=%{version}' herd-classes/META-INF/grolifant5-herd.properties
printf '%s\n' 'Manifest-Version: 1.0' 'Automatic-Module-Name: org.ysb33r.grolifant5.herd' > herd.mf
jar cfm grolifant5-herd.jar herd.mf -C herd-classes .
jar i grolifant5-herd.jar

for jar in grolifant5-core.jar grolifant5-rawhide.jar grolifant5-herd.jar; do
	desc=$(jar --describe-module --file "$jar")
	printf '%s\n' "$desc"
	if printf '%s\n' "$desc" | grep -F -q 'Unable'; then
		exit 1
	fi
done
printf '%s\n' "$desc" | grep -F -q 'org.ysb33r.grolifant5.herd'

cat > grolifant5-rawhide.pom << 'END'
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>org.ysb33r.gradle</groupId>
  <artifactId>grolifant5-rawhide</artifactId>
  <version>5.12.7</version>
  <name>grolifant5-rawhide</name>
  <description>Worker execution helpers for Grolifant.</description>
  <url>https://gitlab.com/ysb33rOrg/gradle/grolifant</url>
  <licenses>
    <license>
      <name>MPL-2.0</name>
      <url>https://www.mozilla.org/en-US/MPL/2.0/</url>
    </license>
  </licenses>
</project>
END

cat > grolifant5-core.pom << 'END'
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>org.ysb33r.gradle</groupId>
  <artifactId>grolifant5-core</artifactId>
  <version>5.12.7</version>
  <name>grolifant5-core</name>
  <description>Building blocks for Gradle plugins.</description>
  <url>https://gitlab.com/ysb33rOrg/gradle/grolifant</url>
  <licenses>
    <license>
      <name>MPL-2.0</name>
      <url>https://www.mozilla.org/en-US/MPL/2.0/</url>
    </license>
  </licenses>
  <dependencies>
    <dependency>
      <groupId>org.ysb33r.gradle</groupId>
      <artifactId>grolifant5-rawhide</artifactId>
      <version>5.12.7</version>
    </dependency>
    <dependency>
      <groupId>commons-io</groupId>
      <artifactId>commons-io</artifactId>
      <version>2.22.0</version>
    </dependency>
    <dependency>
      <groupId>org.apache.ant</groupId>
      <artifactId>ant</artifactId>
      <version>1.10.18</version>
    </dependency>
    <dependency>
      <groupId>org.slf4j</groupId>
      <artifactId>slf4j-api</artifactId>
      <version>2.0.17</version>
    </dependency>
  </dependencies>
</project>
END

cat > grolifant5-herd.pom << 'END'
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>org.ysb33r.gradle</groupId>
  <artifactId>grolifant5-herd</artifactId>
  <version>5.12.7</version>
  <name>grolifant5-herd</name>
  <description>Version marker for the Grolifant herd.</description>
  <url>https://gitlab.com/ysb33rOrg/gradle/grolifant</url>
  <licenses>
    <license>
      <name>MPL-2.0</name>
      <url>https://www.mozilla.org/en-US/MPL/2.0/</url>
    </license>
  </licenses>
</project>
END

%install
set -eo pipefail
sysjar install --buildroot %{buildroot} \
	--artifact grolifant5-rawhide.pom:grolifant5-rawhide.jar \
	--file-name grolifant5-rawhide \
	--filelist .mfiles-rawhide
sysjar install --buildroot %{buildroot} \
	--artifact grolifant5-core.pom:grolifant5-core.jar \
	--file-name grolifant5-core \
	--filelist .mfiles-core
sysjar install --buildroot %{buildroot} \
	--artifact grolifant5-herd.pom:grolifant5-herd.jar \
	--file-name grolifant5-herd \
	--filelist .mfiles-herd
: > .mfiles
for list in .mfiles-rawhide .mfiles-core .mfiles-herd; do
	while IFS= read -r line; do
		grep -qxF "$line" .mfiles || printf '%%s\n' "$line" >> .mfiles
	done < "$list"
done
idx="%{buildroot}/usr/share/sysjar/index/org.ysb33r.gradle/grolifant5-core.sysjar"
test -s "$idx"
grep -F -q '"version": "%{version}"' "$idx"
grep -F -q '"artifactId": "grolifant5-core"' "$idx"
test -s %{buildroot}%{_javadir}/grolifant5-core.jar
test -s %{buildroot}%{_javadir}/grolifant5-rawhide.jar
test -s %{buildroot}%{_javadir}/grolifant5-herd.jar

%check
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
CORE=%{buildroot}%{_javadir}/grolifant5-core.jar
RAWHIDE=%{buildroot}%{_javadir}/grolifant5-rawhide.jar
test -s "$CORE"
test -s "$RAWHIDE"
gradle_cp=
for j in %{_datadir}/gradle/lib/*.jar %{_datadir}/gradle/lib/plugins/*.jar; do
	test -s "$j"
	if [ -z "$gradle_cp" ]; then
		gradle_cp=$j
	else
		gradle_cp=$gradle_cp:$j
	fi
done
CP="$CORE:$RAWHIDE:%{_javadir}/apache-groovy.jar:%{_javadir}/commons-io.jar:%{_javadir}/ant.jar:%{_javadir}/slf4j-api.jar:$gradle_cp"
mkdir -p check
cat > check/Smoke.java << 'EOF'
import org.ysb33r.grolifant5.api.core.CaseFormats;
import org.ysb33r.grolifant5.api.core.GrolifantVersion;
import org.ysb33r.grolifant5.api.remote.worker.WorkerExecutionException;

public class Smoke {
    public static void main(String[] args) {
        String out = CaseFormats.KEBAB_CASE.convertTo(CaseFormats.SNAKE_CASE, "gradle-file");
        if (!"gradle_file".equals(out)) {
            throw new AssertionError(out);
        }
        if (!"%{version}".equals(GrolifantVersion.VERSION)) {
            throw new AssertionError(GrolifantVersion.VERSION);
        }
        WorkerExecutionException ex = new WorkerExecutionException("worker-down");
        if (!"worker-down".equals(ex.getMessage())) {
            throw new AssertionError(ex.getMessage());
        }
        System.out.println("grolifant_ok " + out + " " + GrolifantVersion.VERSION + " " + ex.getMessage());
    }
}
EOF
javac --release 11 -Xlint:-options -cp "$CP" -d check check/Smoke.java
"$JAVA_HOME/bin/java" -cp "check:$CP" Smoke > check/out.txt
cat check/out.txt
grep -F -qx 'grolifant_ok gradle_file %{version} worker-down' check/out.txt

%files -f .mfiles
%doc README.adoc
%license LICENSE
