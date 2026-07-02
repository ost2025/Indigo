# `indigo.loadMolecule` — варианты загрузки

## Общая цепочка вызовов

~~~
indigo.loadMolecule*(...)           ← Python / Java / .NET обёртка
    └─► indigoLoadMoleculeFrom*(…)  ← C API (indigo.dll)
            └─► indigoReadFile / indigoReadString / indigoReadBuffer
                    │
                    │   создаёт IndigoScanner
                    ▼
            indigoLoadMoleculeWithLib(source, -1)
                    │
                    ▼
            MoleculeAutoLoader::loadMolecule()
                    │
                    ▼
            IndigoMolecule  (возвращается как int handle)
~~~

---

## Три варианта C API

Файл: `api/c/indigo/src/indigo_molecule.cpp`

| Вариант | C-функция | Источник данных |
|---|---|---|
| Из строки | `indigoLoadMoleculeFromString(string)` | `BufferScanner(str)` |
| Из файла | `indigoLoadMoleculeFromFile(filename)` | `FileScanner(filename)` |
| Из буфера | `indigoLoadMoleculeFromBuffer(buf, size)` | `BufferScanner(buf, size)` |

Все три сводятся к одной функции `indigoLoadMoleculeWithLib(source, -1)`:

~~~cpp
// indigo_molecule.cpp:487
CEXPORT int indigoLoadMoleculeWithLib(int source, int monomer_library)
{
    INDIGO_BEGIN
    {
        IndigoObject& obj = self.getObject(source);
        MoleculeAutoLoader loader(IndigoScanner::get(obj));

        loader.setOptions(self.loaderOptions());
        loader.dearomatize_on_load = self.dearomatize_on_load;
        loader.arom_options        = self.arom_options;
        loader.input_format        = self.input_format;

        std::unique_ptr<IndigoMolecule> molptr =
            std::make_unique<IndigoMolecule>();

        loader.loadMolecule(molptr->mol, monomer_lib);
        molptr->getProperties().copy(loader.properties);

        return self.addObject(molptr.release()); // ← возвращает handle
    }
    INDIGO_END(-1);
}
~~~

---

## Python-обёртка

Файл: `api/python/indigo/indigo/indigo.py`

~~~python
def loadMolecule(self, string):
    return IndigoObject(
        self,
        IndigoLib.checkResult(
            self._lib().indigoLoadMoleculeFromString(string.encode())
        ),
    )

def loadMoleculeFromFile(self, filename):
    return IndigoObject(
        self,
        IndigoLib.checkResult(
            self._lib().indigoLoadMoleculeFromFile(filename.encode())
        ),
    )

def loadMoleculeFromBuffer(self, data):
    buf = data
    values = (c_byte * len(buf))()
    for i in range(len(buf)):
        values[i] = buf[i]
    return IndigoObject(
        self,
        IndigoLib.checkResult(
            self._lib().indigoLoadMoleculeFromBuffer(values, len(buf))
        ),
    )
~~~

---

## Создание Scanner — `api/c/indigo/src/indigo_io.cpp`

~~~cpp
CEXPORT int indigoReadFile(const char* filename)
{
    INDIGO_BEGIN
    {
        return self.addObject(
            new IndigoScanner(
                new FileScanner(self.filename_encoding, filename)));
    }
    INDIGO_END(-1);
}

CEXPORT int indigoReadString(const char* str)
{
    INDIGO_BEGIN
    {
        return self.addObject(new IndigoScanner(new BufferScanner(str)));
    }
    INDIGO_END(-1);
}

CEXPORT int indigoReadBuffer(const char* buffer, int size)
{
    INDIGO_BEGIN
    {
        return self.addObject(
            new IndigoScanner(new BufferScanner(buffer, size)));
    }
    INDIGO_END(-1);
}
~~~

---

## Что создаётся на выходе

Файл: `api/c/indigo/src/indigo_molecule.h`

~~~cpp
class IndigoMolecule : public IndigoBaseMolecule
{
public:
    Molecule mol;   // ← данные молекулы
};
~~~

Объект добавляется в сессию через `self.addObject()` и возвращается
как целочисленный `handle`.

---

## Автоопределение формата — `MoleculeAutoLoader::_loadMolecule()`

Файл: `core/indigo-core/molecule/src/molecule_auto_loader.cpp`

Порядок детектирования по содержимому потока `Scanner`:

~~~
1. GZip          — сигнатура байт 0x1F 0x8B
2. CDX binary    — заголовок kCDX_HeaderString
3. CDXML         — тег "<CDXML"
4. KET (JSON)    — "{" + "root" + "nodes"
5. Однострочные форматы (Scanner::isSingleLine == true):
   a. InChI      — префикс "InChI="
   b. SMILES     — SmilesLoader (с fallback на SMARTS для query)
   c. IUPAC-имя  — MoleculeNameParser (если SMILES не распознан)
6. По умолчанию  — Molfile / SDF через MolfileLoader
~~~

---

## Пример использования (Python)

~~~python
indigo = Indigo()

# из строки (SMILES)
mol = indigo.loadMolecule("c1ccccc1")

# из файла
mol = indigo.loadMoleculeFromFile("/data/caffeine.mol")

# из буфера
with open("/data/aspirin.mol", "rb") as f:
    mol = indigo.loadMoleculeFromBuffer(f.read())
~~~

---

## Пример использования (Bash heredoc)

~~~bash
python3 - <<'MDEOF'
from indigo import Indigo

indigo = Indigo()

# из строки
mol = indigo.loadMolecule("c1ccccc1.c1ccccc1")
print("atoms:", mol.countAtoms())

# из файла
mol = indigo.loadMoleculeFromFile("/tmp/caffeine.mol")
print("smiles:", mol.smiles())
MDEOF
~~~
